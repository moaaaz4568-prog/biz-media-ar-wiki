#!/usr/bin/env python3
"""evalrun.py — measure recall@k and faithfulness (fix for the "describes
measurement but has no tool" half of gap #2).

Reads eval/questions.yml (known-answer questions), runs the retrieval engine,
and reports: did the expected passage appear in the top-k (recall@k) and —
given a generated answer — what share of its sentences are backed by a
retrieved passage (faithfulness). Measurement is separated from generation
(RETRIEVAL.md): faithfulness is computed against an answer file you supply,
never invented here.

Usage (from knowledge-forge/ root):
    python tools/evalrun.py                     # recall@k for every question
    python tools/evalrun.py -k 10               # different k
    python tools/evalrun.py --answer answers.md # + faithfulness per question
    python tools/evalrun.py --json              # machine-readable
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge.arabic import normalize  # noqa: E402
from kforge.yamlmini import loads  # noqa: E402
import retriever  # noqa: E402

QFILE = 'eval/questions.yml'


def load_questions(root):
    p = os.path.join(root, QFILE)
    if not os.path.isfile(p):
        return [], {}
    cfg = loads(open(p, encoding='utf-8').read()) or {}
    return cfg.get('questions') or [], cfg


def recall_at_k(root, questions, k):
    s = retriever.Searcher(root)
    rows = []
    for q in questions:
        expected = q.get('expected') or []
        expected = [expected] if isinstance(expected, str) else expected
        hits = s.search(q['question'], top_k=k, topic=q.get('topic'))
        hit_paths = set(h['path'] for h in hits)
        got = [e for e in expected if e in hit_paths]
        rows.append({'id': q.get('id', '?'), 'question': q['question'],
                     'expected': expected, 'retrieved': [h['path'] for h in hits],
                     'hit': bool(got), 'hits': got})
    return rows


def sentence_spans(text):
    spans, start = [], 0
    for m in re.finditer(r'[.!?؟]\s', text):
        spans.append((start, m.end()))
        start = m.end()
    if text[start:].strip():
        spans.append((start, len(text)))
    return spans


def faithfulness(root, answer_file, k):
    """Share of answer sentences whose normalized content appears in a retrieved chunk."""
    if not os.path.isfile(answer_file):
        print('answer file not found: %s' % answer_file, file=sys.stderr)
        return None
    text = open(answer_file, encoding='utf-8').read()
    per_q = {}
    cur_id, cur_body = None, []
    for line in text.splitlines():
        m = re.match(r'^##\s*Q:?(\S+)\s*(.*)$', line)
        if m:
            if cur_id:
                per_q[cur_id] = '\n'.join(cur_body)
            cur_id, cur_body = m.group(1), [m.group(2)]
        elif cur_id:
            cur_body.append(line)
    if cur_id:
        per_q[cur_id] = '\n'.join(cur_body)

    s = retriever.Searcher(root)
    questions, _cfg = load_questions(root)
    by_id = {q.get('id', '?'): q for q in questions}
    out = []
    for qid, body in per_q.items():
        q = by_id.get(qid)
        if not q:
            out.append({'id': qid, 'error': 'unknown question id'})
            continue
        chunks = s.search(q['question'], top_k=k, topic=q.get('topic'))
        corpus = normalize(' '.join(c['snippet'] for c in chunks))
        sentences = [normalize(text[a:b]).strip() for a, b in sentence_spans(body)]
        sentences = [x for x in sentences if len(x.split()) >= 3]
        backed = 0
        unbacked = []
        for sent in sentences:
            # a sentence is backed if a 5+ word window of it appears in the corpus
            words = sent.split()
            ok = False
            for i in range(0, max(1, len(words) - 4)):
                if ' '.join(words[i:i + 5]) in corpus:
                    ok = True
                    break
            if ok:
                backed += 1
            else:
                unbacked.append(' '.join(words[:10]))
        out.append({'id': qid, 'sentences': len(sentences), 'backed': backed,
                    'unbacked_examples': unbacked[:3],
                    'faithfulness': round(backed / len(sentences), 3) if sentences else None})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='known-answer evaluation')
    ap.add_argument('-k', '--top-k', type=int, default=10)
    ap.add_argument('--answer', help='markdown of generated answers, "## Q<id>" per question')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    root = os.getcwd()
    questions, cfg = load_questions(root)
    if not questions:
        print('eval/questions.yml has no questions yet — fill it from YOUR content '
              'first (see eval/questions.yml header).')
        return 1
    rows = recall_at_k(root, questions, args.top_k)
    target = (cfg.get('success') or {}).get('recall_at_k', 0.8)
    hits = sum(1 for r in rows if r['hit'])
    recall = hits / len(rows) if rows else 0
    faith = faithfulness(root, args.answer, args.top_k) if args.answer else None
    if args.json:
        print(json.dumps({'k': args.top_k, 'recall_at_k': round(recall, 3),
                          'target': target, 'rows': rows, 'faithfulness': faith},
                         ensure_ascii=False, indent=2))
        return 0
    print('recall@%d = %d/%d = %.3f  (target %.2f)' % (args.top_k, hits, len(rows), recall, target))
    for r in rows:
        print('  %s %s — %s' % ('✓' if r['hit'] else '✗', r['id'], r['question'][:60]))
        if not r['hit']:
            print('     expected: %s | got: %s' % (r['expected'][:3], r['retrieved'][:3]))
    if faith is not None:
        print('\nfaithfulness (vs %s):' % args.answer)
        for f in faith:
            if 'error' in f:
                print('  %s — %s' % (f['id'], f['error']))
            else:
                print('  %s — %d/%d sentences backed (%.0f%%)' % (
                    f['id'], f['backed'], f['sentences'], 100 * (f['faithfulness'] or 0)))
    return 0 if recall >= target else 1


if __name__ == '__main__':
    sys.exit(main())
