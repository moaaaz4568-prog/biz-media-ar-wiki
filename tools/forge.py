#!/usr/bin/env python3
"""forge.py — the one-command operator for knowledge-forge (v2 §8.1).

verify : gates + self-test + unit tests + eval + leak test -> one PASS/FAIL
init   : scaffold a new namespace (folders, INDEX.md files, config, eval set)
build  : run the layer pipeline for a namespace, gating each step
ask    : QUESTION mode — search, cite, answer (constrained generation)
do     : TASK mode — route masters, read them in full, execute
status : what is built per namespace (layers, counts, gates)
graph  : concept/tension entity graph from [[wiki-links]] (RELATIONAL mode)
radar  : contradiction radar — overlapping concepts with opposing polarity

The core loop (verify/init/build without embedding, keyword ask) is
stdlib-only. Dense + LLM are optional rungs; when they are off, forge says
so — never silently (idea 14).
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge import paths, receipts, faith  # noqa: E402
from kforge.frontmatter import split_frontmatter  # noqa: E402
from kforge.yamlmini import loads  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))

LAYER_FOLDERS = [
    ('sources', 'S_'), ('glossary', 'G_'), ('atoms', 'T_'),
    ('concepts', 'C_'), ('tensions', 'X_'), ('masters', 'M_'),
    ('synthesis', 'Y_'), ('rejected', ''), ('eval', ''), ('archive', ''),
]

NOT_IN_SOURCES = 'not in the sources'
# §6.2: the answer tier for expected:[] questions must be EXACTLY this
# sentence — anything else fails the eval.


# ---------------------------------------------------------------- verify

def _has_questions(qfile):
    """True when the eval file holds at least one real question."""
    try:
        t = open(qfile, encoding='utf-8').read()
    except OSError:
        return False
    return bool(re.search(r'^\s+-\s+id:\s*\S+', t, re.M)) and \
        'REPLACE with' not in t


def cmd_verify(args):
    """One PASS/FAIL over: gates self-test, gates check, unit tests, eval
    per namespace, leak test. If verification needs a manual, it is broken."""
    root = paths.repo_root()
    checks = []
    t0 = time.time()

    def run(name, cmd, ok=None):
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
        passed = r.returncode == 0 if ok is None else ok(r)
        tail = (r.stdout or r.stderr).strip().splitlines()
        checks.append({'check': name, 'ok': passed,
                       'detail': tail[-1] if tail else ''})
        return passed, r

    run('gates self-test (D8)', [sys.executable, 'tools/gates.py', 'self-test'])
    run('gates check', [sys.executable, 'tools/gates.py', 'check'])

    # unit tests: count PASS lines (exit may be nonzero on any failure)
    p, r = run('unit tests', [sys.executable, 'tools/tests/run_all.py'])

    kbs = paths.kb_dirs(root)
    if not kbs:
        checks.append({'check': 'namespaces', 'ok': False,
                       'detail': 'no knowledge bases found'})

    for kb in kbs:
        ns = paths.ns_name(kb)
        # skip scaffolds with no questions (root template, fresh inits)
        qfile = os.path.join(kb, 'eval', 'questions.yml')
        if not os.path.isfile(qfile) or not _has_questions(qfile):
            checks.append({'check': 'eval [%s]' % ns, 'ok': True,
                           'detail': 'no questions yet (scaffold) — skipped'})
            continue
        # rebuild indexes so eval measures current files, not stale state
        subprocess.run([sys.executable, 'tools/retriever.py', 'index'],
                       capture_output=True, text=True, cwd=kb)
        run('eval recall@10 [%s]' % ns,
            [sys.executable, 'tools/evalrun.py', '-k', '10',
             '--namespace', ns])
        # leak test: cross-namespace retrieval must return nothing
        leak_ok, leak_detail = leak_test(root)
        checks.append({'check': 'leak test', 'ok': leak_ok,
                       'detail': leak_detail})

    ok = all(c['ok'] for c in checks)
    for c in checks:
        print('  [%s] %-28s %s' % ('PASS' if c['ok'] else 'FAIL',
                                   c['check'], c['detail'][:76]))
    print('\n%s  (%d checks, %.1fs)' % (
        'VERIFY: PASS' if ok else 'VERIFY: FAIL',
        len(checks), time.time() - t0))
    return 0 if ok else 1


def leak_test(root):
    """Idea 1: each namespace has a canary passage carrying a unique
    marker (CANARY-<ns>). A LEAK is namespace A's retrieval returning a
    passage that CONTAINS namespace B's marker — i.e. B's actual text.

    Querying A with B's canary words will naturally hit A's own canary
    (they share boilerplate); that is NOT a leak. Only the marker's
    presence in a returned passage proves cross-namespace content.
    """
    kbs = paths.kb_dirs(root)
    canaries = {}
    for kb in kbs:
        ns = paths.ns_name(kb)
        cpath = os.path.join(kb, 'sources', 'CANARY-%s.md' % ns)
        if not os.path.isfile(cpath):
            continue
        text = open(cpath, encoding='utf-8').read()
        m = re.search(r'CANARY-[a-z0-9-]+', text)
        if m:
            canaries[ns] = (m.group(0), text)
    if len(canaries) < 2:
        return True, 'leak test: %d namespace(s) with canaries — trivially ok' % len(canaries)
    import retriever as R
    leaks = []
    for ns_a, (_mark, _t) in canaries.items():
        kb_a = paths.find_kb(root, ns_a)
        if not os.path.isfile(R.db_path(kb_a)):
            R.build_index(kb_a)   # clean clones have no .kforge/ yet
        s = R.Searcher(kb_a)
        for ns_b, (mark_b, text_b) in canaries.items():
            if ns_a == ns_b:
                continue
            # query with B's canary text (words shared with all canaries
            # included — that is the adversarial part)
            hits = s.search(text_b[:220], top_k=10)
            for h in hits:
                if mark_b in (h.get('text') or '') + (h.get('snippet') or ''):
                    leaks.append('%s returned %s canary text (%s)' % (
                        ns_a, ns_b, h['path']))
    if leaks:
        return False, '; '.join(leaks[:3])
    return True, '%d namespaces x %d canaries — zero cross-ns passages' % (
        len(canaries), len(canaries))


# ---------------------------------------------------------------- init

SCAFFOLD_CFG = """\
# Namespace settings (v2). This file makes the folder a knowledge base:
# one corpus, one voice, one index. Isolation is structural — retrieval
# never crosses namespaces unless you ask for a Y_ synthesis.

namespace: {name}
project:
  name: "{name}"
  language: "{language}"          # ar | en | auto (per-language normalizer)

topics: []                        # list them as you discover them

concept:
  min_words: 250
  max_words: 600
  min_evidence_quotes: 3
  min_limits: 3

master:
  level: L0                       # graduated L0 -> L3 (never start high)
  howto_min_ratio: 0.40
  levels:
    L0: {{sections: 6,  min_words: 2000,  analysis_min_words: 300}}
    L1: {{sections: 10, min_words: 4000,  analysis_min_words: 600}}
    L2: {{sections: 14, min_words: 7000,  analysis_min_words: 1200}}
    L3: {{sections: 18, min_words: 10000, analysis_min_words: 1800}}

retrieval:
  top_k: 10
  recall_at_k_target: 0.8
  engine: auto                    # auto = hybrid when dense available
  fusion: rrf

embedding:                        # optional rung; keyword works without it
  model: e5-small
  dim: 384

eval:
  recall_target: 0.8
"""

CANARY_TMPL = """\
---
type: source
topic: canary
canary: true
---

# CANARY-{name}

CANARY-{name} This passage is a namespace isolation canary. It exists so
the leak test can prove that a query built from namespace {name}'s text
never retrieves passages from another namespace. It carries no knowledge
and is excluded from answers by the canary marker in its front-matter.
"""

EVAL_SKELETON = """\
# Known-answer questions for this namespace. Fill from YOUR content:
# each question's answer must live in a specific passage you can name.
questions:
  - id: q1
    question: "REPLACE with a real question"
    tier: exact                    # exact | paraphrase | comparison
    expected: [sources/S_x.md]
  - id: q2
    question: "REPLACE with a paraphrased question"
    tier: paraphrase
    expected: [sources/S_x.md]
  - id: q3
    question: "REPLACE with a question the sources cannot answer"
    tier: unanswerable
    expected: []
top_k: 10
success:
  recall_at_k: 0.8
  faithfulness: 0.9
"""


def cmd_init(args):
    root = paths.repo_root()
    name = args.name
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name):
        print('namespace name must be lowercase/digits/dashes: %r' % name)
        return 1
    base = os.path.join(root, 'namespaces', name)
    if os.path.isdir(base):
        print('namespace exists already: %s' % base)
        return 1
    os.makedirs(base)
    for folder, _prefix in LAYER_FOLDERS:
        os.makedirs(os.path.join(base, folder), exist_ok=True)
        idx = os.path.join(base, folder, 'INDEX.md')
        if not os.path.isfile(idx):
            open(idx, 'w', encoding='utf-8').write(
                '# Index — %s/\n\n| File | Notes |\n|---|---|\n' % folder)
    open(os.path.join(base, 'config.yml'), 'w', encoding='utf-8').write(
        SCAFFOLD_CFG.format(name=name, language=args.language))
    open(os.path.join(base, 'sources', 'CANARY-%s.md' % name), 'w',
         encoding='utf-8').write(CANARY_TMPL.format(name=name))
    os.makedirs(os.path.join(base, 'eval'), exist_ok=True)
    open(os.path.join(base, 'eval', 'questions.yml'), 'w',
         encoding='utf-8').write(EVAL_SKELETON)
    open(os.path.join(base, 'LOG.md'), 'w', encoding='utf-8').write(
        '| Date | What happened | Measured by | Result |\n|---|---|---|---|\n')
    print('created namespace %s at %s\nnext: add sources, then '
          '`python tools/forge.py build --namespace %s`' % (name, base, name))
    return 0


# ---------------------------------------------------------------- build

def cmd_build(args):
    """Run the pipeline: sources -> glossary -> atoms -> concepts ->
    tensions -> masters -> index, gating after each step.

    Steps with nothing to do report 'nothing to build'. A gate failure
    stops the build naming the file. Auto-generation is a DRAFT — human
    review is required before status: complete (docs/PRINCIPLES.md).
    """
    root = paths.repo_root()
    kb = paths.find_kb(root, args.namespace)
    if kb is None:
        print('namespace %r not found' % args.namespace)
        return 1
    ns = paths.ns_name(kb)

    # 1) index (incremental — cheap, always fresh)
    import retriever as R
    nf, nc, nnew, _u = R.build_index(kb)
    print('[index]   %d files -> %d chunks (%d changed)' % (nf, nc, nnew))

    # 2) layers, in build order (glossary FIRST — v2 §3 layer 1)
    for layer, folder in [('glossary', 'glossary'), ('atoms', 'atoms'),
                          ('concepts', 'concepts'), ('tensions', 'tensions'),
                          ('masters', 'masters')]:
        d = os.path.join(kb, folder)
        n = sum(1 for dp, _dn, fns in os.walk(d) for fn in fns
                if fn.endswith('.md') and fn != 'INDEX.md') \
            if os.path.isdir(d) else 0
        print('[layer]  %-10s %d file(s)' % (layer, n))

    # 3) gates over everything in this namespace
    r = subprocess.run([sys.executable, 'tools/gates.py', 'check',
                        '--namespace', ns], capture_output=True, text=True,
                       cwd=root)
    print(r.stdout.strip())
    if r.returncode != 0:
        print('\nBUILD STOPPED: a gate rejected a file above — fix the FILE, '
              'not the gate (docs/GATES.md).')
        return 1

    # 4) optional dense index (say when it runs, say when it skips)
    cfg = paths.load_cfg(kb)
    want_dense = (cfg.get('embedding') or {}).get('model')
    if want_dense and not args.no_dense:
        r = subprocess.run([sys.executable, 'tools/embed.py', 'index',
                            '--namespace', ns], capture_output=True,
                           text=True, cwd=root)
        if r.returncode == 0:
            out = json.loads(r.stdout or '{}')
            print('[dense]  model=%s +%d vectors (%ss)' % (
                out.get('model'), out.get('embedded_new', 0),
                out.get('seconds')))
        else:
            print('[dense]  SKIPPED (%s) — keyword rung stays on, and '
                  'answers will say so' % (r.stderr or r.stdout or 'error').strip()[:80])
    else:
        print('[dense]  off (no embedding.model in config or --no-dense)')

    # 5) eval (known-answer) — do not expand a base before it passes
    r = subprocess.run([sys.executable, 'tools/evalrun.py', '-k', '10',
                        '--namespace', ns], capture_output=True, text=True,
                       cwd=root)
    print(r.stdout.strip() or '[eval]   no questions yet')
    if r.returncode != 0:
        print('\nBUILD STOPPED: eval below target — fix retrieval before '
              'expanding this namespace (§6.2).')
        return 1
    print('\nBUILD OK [%s]' % ns)
    return 0


# ---------------------------------------------------------------- status

def cmd_status(args):
    root = paths.repo_root()
    kbs = paths.kb_dirs(root)
    print('knowledge-forge status — %d namespace(s)\n' % len(kbs))
    import sqlite3
    for kb in kbs:
        # never descend into sibling namespaces from the repo root
        if os.path.abspath(kb) == os.path.abspath(root):
            walk_top = [os.path.join(root, folder)
                        for folder, _prefix in LAYER_FOLDERS
                        if os.path.isdir(os.path.join(root, folder))]
        else:
            walk_top = [kb]
        ns = paths.ns_name(kb)
        cfg = paths.load_cfg(kb)
        lang = (cfg.get('project') or {}).get('language', '?')
        print('== %s  (language: %s)' % (ns, lang))
        counts = {}
        for top in walk_top:
            for dirpath, _dirs, files in os.walk(top):
                _dirs[:] = [d for d in _dirs if d not in
                            ('.git', 'archive', 'rejected', 'node_modules',
                             'examples', 'namespaces', 'tools', 'docs', '.kforge')]
                for fn in files:
                    if not fn.endswith('.md') or fn in ('INDEX.md', 'LOG.md',
                                                        'questions.yml'):
                        continue
                    p = os.path.join(dirpath, fn)
                    rel = os.path.relpath(p, kb if kb != root else root)
                    layer = rel.split(os.sep)[0]
                    counts[layer] = counts.get(layer, 0) + 1
        for folder, _prefix in LAYER_FOLDERS:
            n = counts.get(folder, 0)
            if n:
                print('   %-10s %3d' % (folder, n))
        db = os.path.join(kb, '.kforge', 'index.db')
        if os.path.isfile(db):
            conn = sqlite3.connect(db)
            nc = conn.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
            print('   %-10s %3d chunks (index.db)' % ('index', nc))
            conn.close()
        vdb = os.path.join(kb, '.kforge', 'vec.db')
        if os.path.isfile(vdb):
            conn = sqlite3.connect(vdb)
            try:
                nv = conn.execute('SELECT COUNT(*) FROM vec_map').fetchone()[0]
                model = conn.execute(
                    "SELECT value FROM vmeta WHERE key='model'").fetchone()
                print('   %-10s %3d vectors (%s)' % (
                    'dense', nv, model[0] if model else '?'))
            except sqlite3.Error:
                pass
            conn.close()
        print()
    return 0


# ---------------------------------------------------------------- graph

def _wiki_links(body):
    return re.findall(r'\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]', body)


def cmd_graph(args):
    """Entity graph from wiki-links (§4.4 RELATIONAL mode).

    Nodes: concepts, tensions, masters, glossary, atoms (per namespace).
    Edges: [[wiki-links]] between entities. Output: edge list + neighbor
    queries. The graph answers who/why-links questions; it never replaces
    retrieval (§3 layer 9).
    """
    root = paths.repo_root()
    kb = paths.find_kb(root, args.namespace) if args.namespace else None
    kbs = [kb] if kb else paths.kb_dirs(root)
    nodes, edges = {}, []
    for kb in kbs:
        ns = paths.ns_name(kb)
        for dirpath, _dirs, files in os.walk(kb):
            _dirs[:] = [d for d in _dirs if d not in ('.git', 'archive', 'rejected')]
            for fn in files:
                if not fn.endswith('.md') or fn in ('INDEX.md', 'LOG.md'):
                    continue
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, kb).replace(os.sep, '/')
                if not re.match(r'(C_|X_|M_|G_|T_|S_|Y_)[^/]*\.md$', rel.split('/')[-1]):
                    continue
                meta, body = split_frontmatter(
                    open(p, encoding='utf-8', errors='replace').read())
                nid = '%s/%s' % (ns, rel)
                nodes[nid] = {'type': meta.get('type', '?'),
                              'topic': meta.get('topic', ''),
                              'ns': ns}
                for link in _wiki_links(body):
                    edges.append((nid, link, ns))
    # resolve link targets to nodes (basename match, same ns first).
    # Wiki-links may omit .md ([[X_send_timing]] not [[X_send_timing.md]]).
    by_base = {}
    for nid in nodes:
        key = nid.split('/')[-1].removesuffix('.md')
        by_base.setdefault(key, []).append(nid)
    resolved = []
    for src, link, ns in edges:
        base = os.path.basename(link.strip()).removesuffix('.md')
        cands = by_base.get(base, [])
        same_ns = [c for c in cands if c.startswith(ns + '/')]
        dst = (same_ns or cands or [None])[0]
        resolved.append((src, dst, link))
    if args.json:
        print(json.dumps({'nodes': nodes,
                          'edges': [{'src': s, 'dst': d, 'raw': r}
                                    for s, d, r in resolved]},
                         ensure_ascii=False, indent=1))
        return 0
    print('graph: %d nodes, %d edges' % (len(nodes), len(resolved)))
    broken = [r for _s, d, r in resolved if d is None]
    if broken:
        print('broken links (%d): %s' % (len(broken), ', '.join(broken[:5])))
    if args.neighbors:
        q = args.neighbors
        match = [n for n in nodes if q.lower() in n.lower()]
        if not match:
            print('no node matches %r' % q)
            return 1
        for n in match:
            outs = [(d, r) for s, d, r in resolved if s == n and d]
            ins = [(s, r) for s, d, r in resolved if d == n]
            print('\n%s  (%s, topic=%s)' % (n, nodes[n]['type'], nodes[n]['topic']))
            for d, r in outs:
                print('   -> %s' % d)
            for s, r in ins:
                print('   <- %s' % s)
            if not outs and not ins:
                print('   (no links)')
    return 0


# ---------------------------------------------------------------- radar

def cmd_radar(args):
    """Contradiction radar (idea 3): propose X_ drafts when two concepts
    overlap in vocabulary but carry opposing polarity. PROPOSES only — a
    human confirms or rejects; never auto-creates a tension."""
    root = paths.repo_root()
    kb = paths.find_kb(root, args.namespace) if args.namespace else None
    kbs = [kb] if kb else paths.kb_dirs(root)
    from kforge.arabic import normalize
    NEG = {'لا', 'never', 'not', 'يزول', 'يذوب', 'ينكسر', 'يضر', 'خطر',
           'يتوقف', 'ينخفض', 'avoid', 'stop', 'drops', 'breaks'}
    POS = {'يكفي', 'يرفع', 'أفضل', 'يحقق', 'success', 'best', 'raises',
           'improves', 'succeeds'}
    for kb in kbs:
        ns = paths.ns_name(kb)
        concepts = {}
        cdir = kb
        for dirpath, _dirs, files in os.walk(os.path.join(kb, 'concepts')):
            for fn in files:
                if fn.startswith('C_') and fn.endswith('.md'):
                    p = os.path.join(dirpath, fn)
                    meta, body = split_frontmatter(open(p, encoding='utf-8').read())
                    concepts[os.path.relpath(p, kb)] = normalize(body)
        names = list(concepts)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = concepts[names[i]], concepts[names[j]]
                wa, wb = set(a.split()), set(b.split())
                overlap = wa & wb - {w for w in wa & wb if len(w) < 3}
                overlap = {w for w in overlap if len(w) >= 3}
                if len(overlap) < args.min_overlap:
                    continue
                pa = bool(POS & wa) and bool(NEG & wa)
                # polarity OPPOSITION: one has a pos word where the other
                # has a neg word over the SAME shared term
                sa = set()
                for w in overlap:
                    if w in POS and w in wb:
                        pass
                a_pos, a_neg = len(POS & wa), len(NEG & wa)
                b_pos, b_neg = len(POS & wb), len(NEG & wb)
                if (a_pos and b_neg) or (a_neg and b_pos):
                    print('[%s] possible tension: %s <-> %s (overlap %d words)' % (
                        ns, names[i].split('/')[-1], names[j].split('/')[-1],
                        len(overlap)))
                    print('    review both, then create tensions/X_xxx.md '
                          '(a human decides — never auto-created)')
    return 0


# ---------------------------------------------------------------- ask / do

SYSTEM_QUESTION = """You answer ONLY from the retrieved passages provided.
Rules:
- Every sentence must be backed by a passage; cite file paths inline like [sources/S_x.md].
- If the passages do not contain the answer, reply exactly: not in the sources
- Show both sides when passages conflict (tensions).
- Answer in the language of the question.
- Never use your training knowledge to fill gaps."""


def _gather_passages(kb, question, top_k, engine, rerank):
    import retriever as R
    s = R.Searcher(kb)
    hits = s.search(question, top_k=top_k, engine=engine, rerank=rerank,
                    expand=True)
    return hits, s.last_engine


def cmd_ask(args):
    root = paths.repo_root()
    kb = paths.find_kb(root, args.namespace)
    if kb is None:
        print('namespace %r not found (have: %s)' % (
            args.namespace,
            ', '.join(paths.ns_name(d) for d in paths.kb_dirs(root))))
        return 1
    ns = paths.ns_name(kb)

    passages, engine_info = _gather_passages(kb, args.question, args.top_k,
                                             args.engine, args.rerank)
    # canary guard: never answer from canary passages (they are probes)
    passages = [p for p in passages if not p['path'].startswith('sources/CANARY-')]

    if not passages:
        print(NOT_IN_SOURCES)
        r = receipts.build(ns, args.question, 'QUESTION',
                           {'retrieval': engine_info.get('retrieval', 'keyword'),
                            'dense': engine_info.get('dense'),
                            'fusion': engine_info.get('fusion'),
                            'rerank': engine_info.get('rerank'), 'llm': None},
                           [], NOT_IN_SOURCES,
                           extra={'reason': 'no passage matched'})
        receipts.save(kb, r)
        return 0

    corpus = '\n\n'.join('[%d] %s # %s\n%s' % (
        i + 1, p['path'], p['heading'], p['text'])
        for i, p in enumerate(passages))
    user = 'QUESTION: %s\n\nPASSAGES:\n%s\n\nAnswer ONLY from the passages, cite paths.' % (
        args.question, corpus)

    from kforge import llm
    if args.no_llm or not llm.available():
        # degradation rung: retrieval-only, with citations, no prose
        print('[retrieval-only rung — LLM unavailable]\n')
        for i, p in enumerate(passages, 1):
            print('%2d. %s # %s' % (i, p['path'], p['heading']))
            print('    %s' % p['snippet'])
        r = receipts.build(ns, args.question, 'QUESTION',
                           {'retrieval': engine_info.get('retrieval'),
                            'dense': engine_info.get('dense'),
                            'fusion': engine_info.get('fusion'),
                            'rerank': engine_info.get('rerank'),
                            'llm': None},
                           passages, '(retrieval-only)')
        receipts.save(kb, r)
        return 0

    try:
        out = llm.chat(SYSTEM_QUESTION, user)
    except llm.LLMUnavailable as e:
        print('[LLM unavailable: %s — retrieval-only rung]\n' % e)
        for i, p in enumerate(passages, 1):
            print('%2d. %s # %s' % (i, p['path'], p['heading']))
            print('    %s' % p['snippet'])
        return 0

    answer = out['content']
    # runtime faithfulness (§5.4): share of sentences backed by passages
    share, total, backed, unbacked = faith.backed_share(answer, corpus)
    f_ok = share is None or share >= args.faith_min
    print(answer)
    print()
    if share is not None and not f_ok:
        print('⚠ UNBACKED SENTENCES (answer below threshold — treat as unsupported):')
        for u in unbacked[:3]:
            print('   - %s' % u)
    if NOT_IN_SOURCES not in answer and share is not None:
        pass
    r = receipts.build(
        ns, args.question, 'QUESTION',
        {'retrieval': engine_info.get('retrieval'),
         'dense': engine_info.get('dense'),
         'fusion': engine_info.get('fusion'),
         'rerank': engine_info.get('rerank'),
         'llm': out.get('model')},
        passages, answer,
        faith={'backed': backed, 'total': total, 'ok': f_ok,
               'share': round(share, 3) if share is not None else None},
        llm=out)
    rid = receipts.save(kb, r)
    print(receipts.render(r))
    return 0


SYSTEM_TASK = """You are executing a task using ONLY the expertise of the
masters provided (read in full below). Rules:
- Execute the task from the masters' expertise; cite file paths for claims.
- Anything the masters do not cover: say "not in the sources".
- Do not use outside knowledge for decisions the masters address.
- Answer in the language of the task."""


def cmd_do(args):
    root = paths.repo_root()
    kb = paths.find_kb(root, args.namespace)
    if kb is None:
        print('namespace %r not found' % args.namespace)
        return 1
    ns = paths.ns_name(kb)
    import retriever as R
    s = R.Searcher(kb)
    routed = s.route(args.task, top_masters=args.masters)
    if not routed:
        print('no master matches this task — the topic is not built yet.\n'
              'propose building it first: sources -> atoms -> concepts -> '
              'master (docs/MASTER_GUIDE.md), then re-run.')
        return 1

    masters_full = []
    for m in routed:
        p = os.path.join(kb, m['path'])
        if os.path.isfile(p):
            masters_full.append((m['path'], open(p, encoding='utf-8').read()))
    corpus = '\n\n'.join('===== MASTER (%s) =====\n%s' % (p, t)
                         for p, t in masters_full)
    user = 'TASK: %s\n\n%s\n\nExecute the task using ONLY these masters.' % (
        args.task, corpus)

    print('reading %d master(s) in full: %s\n' % (
        len(masters_full), ', '.join(p for p, _t in masters_full)))

    from kforge import llm
    if args.no_llm or not llm.available():
        print('[retrieval-only rung — LLM unavailable; masters above are '
              'the expertise. Read them and execute; citations required.]')
        r = receipts.build(ns, args.task, 'TASK',
                           {'retrieval': 'route', 'dense': None,
                            'fusion': None, 'rerank': None, 'llm': None},
                           [{'path': p, 'heading': ''} for p, _t in masters_full],
                           '(masters routed, read in full)',
                           masters_read=[p for p, _t in masters_full])
        receipts.save(kb, r)
        return 0
    try:
        out = llm.chat(SYSTEM_TASK, user)
    except llm.LLMUnavailable as e:
        print('[LLM unavailable: %s — masters above; execute from them]' % e)
        return 0

    print(out['content'])
    r = receipts.build(
        ns, args.task, 'TASK',
        {'retrieval': 'route', 'dense': None, 'fusion': None,
         'rerank': None, 'llm': out.get('model')},
        [{'path': p, 'heading': ''} for p, _t in masters_full],
        out['content'], masters_read=[p for p, _t in masters_full], llm=out)
    receipts.save(kb, r)
    print()
    print(receipts.render(r))
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description='knowledge-forge operator')
    sub = ap.add_subparsers(dest='cmd', required=True)

    sub.add_parser('verify', help='gates + tests + eval + leak test -> one PASS/FAIL')

    i = sub.add_parser('init', help='scaffold a namespace')
    i.add_argument('name')
    i.add_argument('--language', default='auto')

    b = sub.add_parser('build', help='run the pipeline, gating each step')
    b.add_argument('--namespace', required=True)
    b.add_argument('--no-dense', action='store_true')

    sub.add_parser('status', help='what is built, per namespace')

    a = sub.add_parser('ask', help='QUESTION mode: search -> cite -> answer')
    a.add_argument('question')
    a.add_argument('--namespace', required=True)
    a.add_argument('-k', '--top-k', type=int, default=8)
    a.add_argument('--engine', choices=['auto', 'keyword', 'hybrid'],
                   default='auto')
    a.add_argument('--rerank', action='store_true')
    a.add_argument('--no-llm', action='store_true',
                   help='retrieval-only rung (passages + citations, no prose)')
    a.add_argument('--faith-min', type=float, default=0.9)

    d = sub.add_parser('do', help='TASK mode: route -> read masters -> execute')
    d.add_argument('task')
    d.add_argument('--namespace', required=True)
    d.add_argument('-m', '--masters', type=int, default=3)
    d.add_argument('--no-llm', action='store_true')

    g = sub.add_parser('graph', help='entity graph from wiki-links')
    g.add_argument('--namespace')
    g.add_argument('--neighbors', help='show in/out links of a node')
    g.add_argument('--json', action='store_true')

    rd = sub.add_parser('radar', help='contradiction radar (proposes X_ drafts)')
    rd.add_argument('--namespace')
    rd.add_argument('--min-overlap', type=int, default=8)

    args = ap.parse_args(argv)
    return {'verify': cmd_verify, 'init': cmd_init, 'build': cmd_build,
            'status': cmd_status, 'ask': cmd_ask, 'do': cmd_do,
            'graph': cmd_graph, 'radar': cmd_radar}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
