"""llm.py — the optional answering model as a thin bridge.

Constrained generation (§5) needs an LLM at ANSWER time only. The core loop
(gates + keyword retrieval + eval) never calls this module, so the repo
stays stdlib-only (§11: no paid API needed for the core loop).

The bridge wraps the locally configured `z-ai` CLI. If the CLI is absent or
fails, LLMUnavailable is raised and the caller degrades to retrieval-only
mode (idea 14) — and says so in the answer receipt.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time

BIN = 'z-ai'
TIMEOUT = 300  # masters can be long; generation is not the fast path


class LLMUnavailable(Exception):
    pass


def available():
    return shutil.which(BIN) is not None


def chat(system, user, timeout=TIMEOUT):
    """One-shot chat completion. Returns dict(content, model, usage, ms).

    Raises LLMUnavailable when the bridge is missing or errors — callers
    must treat that as a rung downgrade, never as a crash.
    """
    if not available():
        raise LLMUnavailable('%s CLI not found' % BIN)
    fd, out = tempfile.mkstemp(suffix='.json', prefix='kf_llm_')
    os.close(fd)
    try:
        cmd = [BIN, 'chat', '-p', user, '-o', out]
        if system:
            cmd += ['-s', system]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
        ms = int((time.time() - t0) * 1000)
        if r.returncode != 0 or not os.path.isfile(out):
            raise LLMUnavailable('bridge exit %d: %s' % (
                r.returncode, (r.stderr or r.stdout or '')[:200]))
        d = json.load(open(out, encoding='utf-8'))
        content = (d.get('choices') or [{}])[0].get('message', {}).get('content', '')
        if not content:
            raise LLMUnavailable('empty completion')
        return {'content': content.strip(),
                'model': d.get('model', 'unknown'),
                'usage': d.get('usage', {}),
                'ms': ms}
    except subprocess.TimeoutExpired:
        raise LLMUnavailable('bridge timeout after %ss' % timeout)
    finally:
        try:
            os.unlink(out)
        except OSError:
            pass
