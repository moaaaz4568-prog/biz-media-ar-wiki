"""receipts.py — answer receipts (idea 9).

Every answer carries a receipt: namespace, retrieved passage IDs + ranks,
engine rung, model, timestamp, latency, tokens, runtime faithfulness.
Receipts make answers reproducible and misses debuggable — a miss without a
receipt cannot be fixed. Saved under <kb>/.kforge/receipts/ (generated,
gitignored) and printed with every answer.
"""

import json
import os
import re
import time


def build(namespace, question, mode, engine, passages, answer,
          masters_read=None, llm=None, faith=None, extra=None):
    r = {
        'version': 1,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'namespace': namespace,
        'mode': mode,                    # QUESTION | TASK | COMPARISON | RELATIONAL
        'question': question,
        'engine': engine,                # e.g. {'retrieval': 'hybrid', 'dense': 'e5-small',
                                         #  'fusion': 'rrf', 'rerank': False, 'llm': 'glm-4-plus'|None}
        'passages': [{'rank': i + 1, 'path': p['path'], 'heading': p.get('heading', ''),
                      'score': p.get('score')} for i, p in enumerate(passages)],
        'answer_chars': len(answer or ''),
    }
    if masters_read:
        r['masters_read_in_full'] = masters_read
    if llm:
        r['latency_ms'] = llm.get('ms')
        r['tokens'] = llm.get('usage')
    if faith:
        r['faithfulness'] = faith
    if extra:
        r.update(extra)
    return r


def render(r):
    lines = [
        '--- answer receipt ---',
        'namespace : %s   mode: %s   %s' % (r['namespace'], r['mode'], r['timestamp']),
        'engine    : retrieval=%s dense=%s fusion=%s rerank=%s llm=%s' % (
            r['engine'].get('retrieval'), r['engine'].get('dense'),
            r['engine'].get('fusion'), r['engine'].get('rerank'),
            r['engine'].get('llm') or 'none (retrieval-only rung)'),
    ]
    if r.get('masters_read_in_full'):
        lines.append('masters   : read in full: %s' % ', '.join(r['masters_read_in_full']))
    lines.append('passages  :')
    for p in r['passages']:
        lines.append('  %2d. %s%s' % (p['rank'], p['path'],
                                       ' (%s)' % p['heading'] if p.get('heading') else ''))
    if 'faithfulness' in r and r['faithfulness']:
        f = r['faithfulness']
        lines.append('faithful  : %s/%s sentences backed%s' % (
            f.get('backed'), f.get('total'),
            '' if f.get('ok') else '  << BELOW THRESHOLD — treat as unsupported'))
    if r.get('latency_ms') is not None:
        lines.append('latency   : %s ms   tokens: %s' % (
            r['latency_ms'], r.get('tokens')))
    lines.append('receipt id: %s' % r.get('id', '-'))
    return '\n'.join(lines)


def save(kb, r):
    """Persist under <kb>/.kforge/receipts/. Returns the receipt id (or None)."""
    d = os.path.join(kb, '.kforge', 'receipts')
    os.makedirs(d, exist_ok=True)
    slug = re.sub(r'\W+', '-', (r.get('question') or 'q').strip())[:40].strip('-') or 'q'
    ts = time.strftime('%Y%m%d-%H%M%S')
    rid = '%s-%s' % (ts, slug)
    r['id'] = rid
    p = os.path.join(d, rid + '.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    return rid
