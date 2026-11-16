#!/usr/bin/env python3
"""evalrun.py — measure recall@k and faithfulness (fix for the "describes
measurement but has no tool" half of gap #2).

Reads eval/questions.yml (known-answer questions), runs the retrieval engine,
and reports: did the expected passage appear in the top-k (recall@k) and —
given a generated answer — what share of its sentences are backed by a
retrieved passage (faithfulness). Measurement is separated from generation
(RETRIEVAL.md): faithfulness is computed against an answer file you supply,
never invented here.

v2 (idea 8 — graduated evaluation):
- Questions carry a `tier:` field: exact | paraphrase | comparison |
  unanswerable. Recall is reported PER TIER — never one blended number
  (a blended 0.9 can hide paraphrase at 0.4). Questions without a tier
  default to 'exact' (v1 sets stay valid).
- `--engine` compares keyword vs hybrid on the SAME set: the winner is a
  measured number in LOG, not a claim.
- `--compare-engines` runs both and prints the side-by-side table.

Usage (from a KB root, or repo root with --namespace):
    python tools/evalrun.py                        # recall@10, all tiers
    python tools/evalrun.py -k 10 --namespace N
    python tools/evalrun.py --engine hybrid        # one engine
    python tools/evalrun.py --compare-engines      # keyword vs hybrid
    python tools/evalrun.py --answer answers.md    # + faithfulness
    python tools/evalrun.py --json                 # machine-readable
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge import faith  # noqa: E402
from kforge import paths  # noqa: E402
from kforge.yamlmini import loads  # noqa: E402
import retriever  # noqa: E402

QFILE = 'eval/questions.yml'
TIERS = ('exact', 'paraphrase', 'comparison', 'unanswerable')


def load_questions(root):
    p = os.path.join(root, QFILE)
    if not os.path.isfile(p):
        return [], {}
    cfg = loads(open(p, encoding='utf-8').read()) or {}
    return cfg.get('questions') or [], cfg


def recall_at_k(root, questions, k, engine='auto', rerank=False):
    """Per-question hit rows + per-tier recall. engine: keyword|hybrid|auto."""
    s = retriever.Searcher(root)
    rows = []
    for q in questions:
        expected = q.get('expected') or []
        expected = [expected] if isinstance(expected, str) else expected
        hits = s.search(q['question'], top_k=k, topic=q.get('topic'),
                        engine=engine, rerank=rerank)
        hit_paths = set(h['path'] for h in hits)
        got = [e for e in expected if e in hit_paths]
        rows.append({'id': q.get('id', '?'), 'question': q['question'],
                     'tier': q.get('tier') or 'exact',
                     'expected': expected,
                     'retrieved': [h['path'] for h in hits],
                     'hit': bool(got) if expected else None,
                     'hits': got})
    return rows


def per_tier(rows):
    """recall per tier. Unanswerable (expected: []) counts a hit when the
    engine returns NOTHING relevant... which retrieval alone cannot prove;
    by convention those rows score hit=None and are reported as counts."""
    out = {}
    for tier in TIERS:
        sub = [r for r in rows if r['tier'] == tier and r['hit'] is not None]
        if not sub:
            continue
        hits = sum(1 for r in sub if r['hit'])
        out[tier] = {'n': len(sub), 'hits': hits,
                     'recall': round(hits / len(sub), 3)}
    unans = [r for r in rows if r['tier'] == 'unanswerable']
    if unans:
        out['unanswerable'] = {
            'n': len(unans),
            'returned_results': sum(1 for r in unans if r['retrieved']),
            'note': 'expected: [] — generation must say "not in the sources"'}
    return out


def _answer_key_hack(text):
    per_q = {}
    cur_id, cur_body = None, []
    for line in text.splitlines():
        if line.startswith('## Q') or line.startswith('##q'):
            if cur_id:
                per_q[cur_id] = '\n'.join(cur_body)
            cur_id = line.lstrip('# ').split()[0].lstrip('Qq:')
            cur_id = cur_id.strip(':')
            cur_body = []
        elif cur_id:
            cur_body.append(line)
    if cur_id:
        per_q[cur_id] = '\n'.join(cur_body)
    return per_q


def faithfulness(root, answer_file, k, engine='auto'):
    """Share of answer sentences backed by a retrieved passage."""
    if not os.path.isfile(answer_file):
        print('answer file not found: %s' % answer_file, file=sys.stderr)
        return None
    text = open(answer_file, encoding='utf-8').read()
    per_q = _answer_key_hack(text)

    s = retriever.Searcher(root)
    questions, _cfg = load_questions(root)
    by_id = {q.get('id', '?'): q for q in questions}
    out = []
    for qid, body in per_q.items():
        q = by_id.get(qid)
        if not q:
            out.append({'id': qid, 'error': 'unknown question id'})
            continue
        chunks = s.search(q['question'], top_k=k, topic=q.get('topic'),
                          engine=engine)
        corpus = ' '.join(c.get('text', c.get('snippet', '')) for c in chunks)
        share, total, backed, unbacked = faith.backed_share(body, corpus)
        out.append({'id': qid, 'sentences': total, 'backed': backed,
                    'unbacked_examples': unbacked[:3],
                    'faithfulness': round(share, 3) if share is not None else None})
    return out


def _root_for(args):
    root = paths.repo_root()
    if args.namespace:
        kb = paths.find_kb(root, args.namespace)
        if kb is None:
            print('namespace %r not found' % args.namespace, file=sys.stderr)
            return None
        return kb
    cwd = os.getcwd()
    if os.path.isfile(os.path.join(cwd, 'config.yml')) and \
            os.path.abspath(cwd) != os.path.abspath(root):
        return cwd
    # single-KB repos: fall back to repo root itself
    return root


def run_engine(root, args, engine):
    questions, cfg = load_questions(root)
    rows = recall_at_k(root, questions, args.top_k, engine=engine,
                       rerank=args.rerank)
    tiers = per_tier(rows)
    answerable = [r for r in rows if r['hit'] is not None]
    hits = sum(1 for r in answerable if r['hit'])
    overall = round(hits / len(answerable), 3) if answerable else 0
    return {'questions': questions, 'rows': rows, 'tiers': tiers,
            'overall': overall, 'target': (cfg.get('success') or {}).get(
                'recall_at_k', 0.8)}


def main(argv=None):
    ap = argparse.ArgumentParser(description='known-answer evaluation')
    ap.add_argument('-k', '--top-k', type=int, default=10)
    ap.add_argument('--namespace')
    ap.add_argument('--engine', choices=['keyword', 'hybrid', 'auto'],
                    default='auto')  # auto = the namespace's configured engine
    ap.add_argument('--rerank', action='store_true')
    ap.add_argument('--compare-engines', action='store_true',
                    help='run keyword AND hybrid, print side-by-side')
    ap.add_argument('--answer', help='markdown of generated answers, "## Q<id>" per question')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    root = _root_for(args)
    if root is None:
        return 1
    questions, _cfg = load_questions(root)
    if not questions:
        print('eval/questions.yml has no questions yet — fill it from YOUR content '
              'first (see eval/questions.yml header).')
        return 1

    if args.compare_engines:
        kw = run_engine(root, args, 'keyword')
        hy = run_engine(root, args, 'hybrid')
        print('engine comparison — recall@%d per tier (same questions):'
              % args.top_k)
        print('  %-16s %-22s %-22s' % ('tier', 'keyword', 'hybrid'))
        tiers = sorted(set(kw['tiers']) | set(hy['tiers']))
        for t in tiers:
            k_t = kw['tiers'].get(t, {})
            h_t = hy['tiers'].get(t, {})
            k_s = ('%d/%d = %.3f' % (k_t.get('hits', 0), k_t.get('n', 0),
                                     k_t.get('recall', 0))) if k_t else '-'
            h_s = ('%d/%d = %.3f' % (h_t.get('hits', 0), h_t.get('n', 0),
                                     h_t.get('recall', 0))) if h_t else '-'
            print('  %-16s %-22s %-22s' % (t, k_s, h_s))
        print('  %-16s %-22s %-22s' % (
            'OVERALL', '%.3f' % kw['overall'], '%.3f' % hy['overall']))
        winner = 'hybrid' if hy['overall'] >= kw['overall'] else 'keyword'
        print('\nwinner (overall): %s — record it in LOG.md with this command'
              % winner)
        if args.json:
            print(json.dumps({'keyword': {'tiers': kw['tiers'],
                                          'overall': kw['overall']},
                              'hybrid': {'tiers': hy['tiers'],
                                         'overall': hy['overall']}},
                             ensure_ascii=False, indent=2))
        return 0

    res = run_engine(root, args, args.engine)
    rows, tiers = res['rows'], res['tiers']
    target = res['target']
    answerable = [r for r in rows if r['hit'] is not None]
    hits = sum(1 for r in answerable if r['hit'])
    recall = hits / len(answerable) if answerable else 0
    faith_rows = faithfulness(root, args.answer, args.top_k, args.engine) \
        if args.answer else None
    if args.json:
        print(json.dumps({'k': args.top_k, 'engine': args.engine,
                          'recall_at_k': round(recall, 3), 'target': target,
                          'tiers': tiers, 'rows': rows,
                          'faithfulness': faith_rows},
                         ensure_ascii=False, indent=2))
        return 0
    print('engine=%s  recall@%d = %d/%d = %.3f  (target %.2f)' % (
        args.engine, args.top_k, hits, len(answerable), recall, target))
    for t in TIERS:
        if t in tiers and t != 'unanswerable':
            d = tiers[t]
            print('  %-12s %d/%d = %.3f' % (t, d['hits'], d['n'], d['recall']))
    if 'unanswerable' in tiers:
        d = tiers['unanswerable']
        print('  %-12s %d question(s), %d returned results (generation must '
              'still say "not in the sources")' % (
                  'unanswerable', d['n'], d['returned_results']))
    for r in rows:
        if r['hit'] is False:
            print('  ✗ %s [%s] — %s' % (r['id'], r['tier'], r['question'][:60]))
            print('     expected: %s | got: %s' % (
                r['expected'][:3], r['retrieved'][:3]))
    if faith_rows is not None:
        print('\nfaithfulness (vs %s):' % args.answer)
        for f in faith_rows:
            if 'error' in f:
                print('  %s — %s' % (f['id'], f['error']))
            else:
                print('  %s — %d/%d sentences backed (%.0f%%)' % (
                    f['id'], f['backed'], f['sentences'], 100 * (f['faithfulness'] or 0)))
    # per-tier pass: every answerable tier >= target
    tier_ok = all(d['recall'] >= target
                  for t, d in tiers.items() if t != 'unanswerable')
    return 0 if (recall >= target and tier_ok) else 1


if __name__ == '__main__':
    sys.exit(main())
