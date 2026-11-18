#!/usr/bin/env python3
"""retriever.py — the retrieval engine: BM25 core, hybrid optional (v2 §4).

v1 (kept, stdlib-only): SQLite index over every layer, BM25 over
language-normalized tokens, QUESTION search + TASK route.

v2 additions:
- Incremental indexing (idea 10): a per-file sha1 table; only changed files
  re-chunk. Full rebuild stays one command: `index --force`.
- Hybrid retrieval (§4.2/4.3): fuse BM25 with dense vectors from
  <kb>/.kforge/vec.db (see embed.py) via RRF or weighted sum, optional
  cross-encoder rerank, optional section expansion for broad questions.
  Degrades to keyword-only when the dense rung is off — and reports it.
- Namespaces (§7): each KB directory has its OWN .kforge/index.db, so
  isolation is structural. `--namespace` resolves which KB to search.

Usage (from a KB root, or repo root with --namespace):
    python tools/retriever.py index [--force]
    python tools/retriever.py search "query" -k 10 [--namespace N]
    python tools/retriever.py search "query" --engine hybrid [--rerank] [--expand]
    python tools/retriever.py route "task" -m 3
    python tools/retriever.py status
"""

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge.frontmatter import split_frontmatter  # noqa: E402
from kforge import paths  # noqa: E402

DB_DIR = '.kforge'
CHUNK_WORDS = 400          # max words per chunk (sections split beyond this)
MIN_TOKENS_FOR_MATCH = 1   # a chunk must share at least this many query tokens
FUSE_K = 60                # RRF constant
FUSE_CANDIDATES = 30       # candidates taken from EACH list before fusion

LAYER_BY_FOLDER = {
    'sources': 'source', 'atoms': 'atom', 'concepts': 'concept',
    'tensions': 'tension', 'glossary': 'glossary', 'masters': 'master',
    'synthesis': 'synthesis',
}
_HEADING_RE = re.compile(r'^#{1,4}\s+(.*?)\s*$', re.M)

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, path TEXT, heading TEXT,
    layer TEXT, topic TEXT, nwords INTEGER, text TEXT);
CREATE TABLE IF NOT EXISTS postings(term TEXT, chunk_id INTEGER, tf INTEGER);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value INTEGER, extra TEXT);
CREATE TABLE IF NOT EXISTS fstate(path TEXT PRIMARY KEY, sha1 TEXT);
CREATE INDEX IF NOT EXISTS idx_postings_term ON postings(term);
CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
"""

EXCLUDED_DIRS = ('.git', DB_DIR, 'archive', 'rejected', 'node_modules',
                 'tools', 'docs', 'examples', 'namespaces', 'eval', 'audit')


def db_path(root):
    return os.path.join(root, DB_DIR, 'index.db')


def _sections(md_text):
    """Split a markdown file into (heading, text) sections."""
    marks = list(_HEADING_RE.finditer(md_text))
    if not marks:
        return [('', md_text)]
    out = []
    if md_text[:marks[0].start()].strip():
        out.append(('', md_text[:marks[0].start()]))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(md_text)
        # section text EXCLUDES the heading line itself (it is stored in the
        # heading column); keeping it in text made snippets start with a repeat
        out.append((m.group(1), md_text[m.end():end]))
    return out


def _chunks(heading, text):
    """Split a long section into ~CHUNK_WORDS word pieces on paragraph bounds."""
    paras = text.split('\n\n')
    chunks, cur, cur_words = [], [], 0
    for p in paras:
        w = len(p.split())
        if cur and cur_words + w > CHUNK_WORDS:
            chunks.append((heading, '\n\n'.join(cur)))
            cur, cur_words = [], 0
        cur.append(p)
        cur_words += w
    if cur:
        chunks.append((heading, '\n\n'.join(cur)))
    return chunks or [(heading, text)]


def _layer_topic(root, path):
    rel = os.path.relpath(path, root).replace(os.sep, '/')
    parts = rel.split('/')
    layer = LAYER_BY_FOLDER.get(parts[0], '')
    topic = ''
    if len(parts) >= 3 and parts[0] in ('atoms', 'concepts', 'masters'):
        topic = parts[1]
    return layer, topic, rel


def _walk_md(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for fn in sorted(files):
            if fn.endswith('.md') and fn not in ('INDEX.md', 'LOG.md',
                                                 'TOPIC.md', 'USAGE.md',
                                                 'HOME.md', 'HISTORY.md'):
                yield os.path.join(dirpath, fn)


def _tokenizer_for(root):
    """Language-aware tokenization (idea 13): per-KB config picks the plugin."""
    cfg = paths.load_cfg(root)
    from kforge import langs
    _n, tok = langs.for_language(
        (cfg.get('project') or {}).get('language', cfg.get('language')))
    return tok


def build_index(root, force=False):
    """(Re)build the BM25 index. Incremental by file content hash.

    Only files whose sha1 changed are re-chunked; vanished files are
    pruned. `force` drops everything first (the one-command full rebuild).
    """
    tokenize = _tokenizer_for(root)
    os.makedirs(os.path.join(root, DB_DIR), exist_ok=True)
    fresh = not os.path.isfile(db_path(root))
    conn = sqlite3.connect(db_path(root))
    conn.executescript(SCHEMA)
    if force or fresh:
        conn.executescript('DROP TABLE IF EXISTS chunks; DROP TABLE IF EXISTS postings;'
                           ' DROP TABLE IF EXISTS meta; DROP TABLE IF EXISTS fstate;')
        conn.executescript(SCHEMA)

    prev = {p: s for p, s in conn.execute('SELECT path, sha1 FROM fstate')}
    seen = {}
    n_files = n_new = n_unchanged = 0
    for p in _walk_md(root):
        raw = open(p, encoding='utf-8', errors='replace').read()
        sha = hashlib.sha1(raw.encode('utf-8', 'replace')).hexdigest()
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        seen[rel] = sha
        n_files += 1
        if prev.get(rel) == sha:
            n_unchanged += 1
            continue
        # changed or new: drop old chunks/postings for this path, re-chunk
        conn.execute('DELETE FROM postings WHERE chunk_id IN '
                     '(SELECT id FROM chunks WHERE path=?)', (rel,))
        conn.execute('DELETE FROM chunks WHERE path=?', (rel,))
        _meta, body = split_frontmatter(raw)
        _layer, _topic, _ = _layer_topic(root, p)
        for heading, sec in _sections(body):
            for h, piece in _chunks(heading, sec):
                toks = tokenize(piece)
                if not toks:
                    continue
                cur = conn.execute(
                    'INSERT INTO chunks(path,heading,layer,topic,nwords,text)'
                    ' VALUES(?,?,?,?,?,?)',
                    (rel, heading, _layer, _topic, len(piece.split()), piece))
                counts = {}
                for t in toks:
                    counts[t] = counts.get(t, 0) + 1
                conn.executemany('INSERT INTO postings VALUES(?,?,?)',
                                 [(t, cur.lastrowid, c) for t, c in counts.items()])
        n_new += 1
    # prune files that vanished
    for rel in set(prev) - set(seen):
        conn.execute('DELETE FROM postings WHERE chunk_id IN '
                     '(SELECT id FROM chunks WHERE path=?)', (rel,))
        conn.execute('DELETE FROM chunks WHERE path=?', (rel,))
        conn.execute('DELETE FROM fstate WHERE path=?', (rel,))
    conn.executemany('INSERT OR REPLACE INTO fstate VALUES(?,?)', seen.items())
    n_chunks = conn.execute('SELECT COUNT(*) FROM chunks').fetchone()[0]
    conn.executemany('INSERT OR REPLACE INTO meta VALUES(?,?,?)', [
        ('files', n_files, ''), ('chunks', n_chunks, ''),
        ('total_words', conn.execute(
            'SELECT SUM(nwords) FROM chunks').fetchone()[0] or 0, ''),
        ('namespace', 1, paths.ns_name(root))])
    conn.commit()
    conn.close()
    return n_files, n_chunks, n_new, n_unchanged


class Searcher:
    """BM25 + optional dense fusion over ONE namespace's index."""

    def __init__(self, root):
        self.root = root
        self.conn = sqlite3.connect(db_path(root))
        self.conn.row_factory = sqlite3.Row
        m = {r['key']: r['value'] for r in self.conn.execute('SELECT * FROM meta')}
        self.N = m.get('chunks', 0)
        self.avgdl = (m.get('total_words', 0) / self.N) if self.N else 0
        self.tokenize = _tokenizer_for(root)
        self.last_engine = {'retrieval': 'keyword', 'dense': None,
                            'fusion': None, 'rerank': None}
        self._dense_model = None  # resolved lazily, only when hybrid is asked

    # ---------- BM25 ----------

    def _bm25(self, query, top_n, topic=None, layer=None):
        toks = self.tokenize(query)
        if not toks or not self.N:
            return []
        q = 'SELECT p.term, p.chunk_id, p.tf FROM postings p WHERE p.term IN (%s)' % \
            ','.join('?' * len(toks))
        rows = self.conn.execute(q, toks).fetchall()
        by_chunk, df = {}, {}
        for r in rows:
            df[r['term']] = df.get(r['term'], 0) + 1
            by_chunk.setdefault(r['chunk_id'], {})[r['term']] = r['tf']
        k1, b, scores = 1.5, 0.75, {}
        for cid, tfs in by_chunk.items():
            if len(tfs) < MIN_TOKENS_FOR_MATCH:
                continue
            ch = self.conn.execute('SELECT * FROM chunks WHERE id=?', (cid,)).fetchone()
            if topic and ch['topic'] != topic:
                continue
            if layer and ch['layer'] != layer:
                continue
            dl = ch['nwords'] or 1
            s = 0.0
            for t, tf in tfs.items():
                idf = math.log(1 + (self.N - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / self.avgdl))
            scores[cid] = s
        return sorted(scores.items(), key=lambda x: -x[1])[:top_n]

    # ---------- dense ----------

    def _dense(self, query, top_n):
        """[(chunk_id, similarity)] via embed.dense_search; None if rung off."""
        try:
            import embed as embed_mod
            if self._dense_model is None:
                conn, meta = embed_mod.open_vec_store(self.root)
                if conn is not None:
                    conn.close()
                if meta.get('model'):
                    self._dense_model = meta.get('model')
                else:
                    self._dense_model = False
            if self._dense_model is False:
                return None
            hits, model = embed_mod.dense_search(self.root, query, top_n)
            self.last_engine['dense'] = model
            return hits
        except Exception:
            return None

    # ---------- fusion + rerank ----------

    @staticmethod
    def _rrf(lists, k=FUSE_K):
        """Reciprocal rank fusion: score = sum 1/(k + rank)."""
        out = {}
        for lst in lists:
            for rank, (cid, _s) in enumerate(lst, 1):
                out[cid] = out.get(cid, 0.0) + 1.0 / (k + rank)
        return out

    @staticmethod
    def _weighted(lists, weights):
        """Weighted sum of min-max-normalized scores."""
        out = {}
        for lst, w in zip(lists, weights):
            if not lst:
                continue
            lo = min(s for _c, s in lst)
            hi = max(s for _c, s in lst)
            span = (hi - lo) or 1.0
            for cid, s in lst:
                out[cid] = out.get(cid, 0.0) + w * (s - lo) / span
        return out

    def _rerank(self, query, cands):
        """Cross-encoder rerank of [(cid, score)]. Returns (list, ok)."""
        try:
            import embed as embed_mod
            rr = embed_mod.get_reranker()
            texts = [self._chunk(cid)['text'] for cid, _s in cands]
            scores = rr.score(query, texts)
            self.last_engine['rerank'] = rr.name
            return sorted(zip(cands, scores), key=lambda x: -x[1]), True
        except Exception:
            self.last_engine['rerank'] = None
            return None, False

    def _chunk(self, cid):
        return self.conn.execute('SELECT * FROM chunks WHERE id=?', (cid,)).fetchone()

    # ---------- public API ----------

    def search(self, query, top_k=10, topic=None, layer=None, engine='auto',
               rerank=False, expand=False):
        """Ranked passages. engine: 'keyword' | 'hybrid' | 'dense' | 'auto'.

        'auto' uses config retrieval.engine when set, else hybrid-if-possible
        with fallback to keyword (last_engine says which rung ran — never
        silent, per idea 14).
        """
        cfg = paths.load_cfg(self.root).get('retrieval', {})
        if engine == 'auto':
            # config 'engine: auto' means hybrid-if-available (else keyword);
            # an explicit config value (keyword/hybrid/dense) is honored as-is
            engine = cfg.get('engine') or 'hybrid'
            if engine == 'auto':
                engine = 'hybrid'

        self.last_engine = {'retrieval': 'keyword', 'dense': None,
                            'fusion': None, 'rerank': None}
        lists = []
        if engine in ('keyword', 'hybrid'):
            lists.append(self._bm25(
                query, FUSE_CANDIDATES if engine == 'hybrid' else top_k,
                topic, layer))
        if engine in ('hybrid', 'dense'):
            dn = self._dense(query, FUSE_CANDIDATES if engine == 'hybrid'
                             else max(top_k, FUSE_CANDIDATES))
            if dn is None:
                if engine == 'dense':
                    return []
            else:
                # topic/layer filters apply to dense hits too (same KB, same rules)
                if topic or layer:
                    dn = [(cid, s) for cid, s in dn
                          if (not topic or self._chunk(cid)['topic'] == topic)
                          and (not layer or self._chunk(cid)['layer'] == layer)]
                lists.append(dn)
                self.last_engine['retrieval'] = 'hybrid'

        nonempty = [l for l in lists if l]
        if not nonempty:
            return []
        if len(nonempty) == 1:
            ranked = nonempty[0][:top_k]
            self.last_engine['retrieval'] = ('hybrid' if self.last_engine['dense']
                                             and engine == 'hybrid' else
                                             self.last_engine['retrieval'])
        else:
            how = cfg.get('fusion', 'rrf')
            if how == 'weighted':
                scores = self._weighted(lists, cfg.get('fusion_weights', [0.5, 0.5]))
            else:
                how = 'rrf'
                scores = self._rrf(lists)
            self.last_engine['fusion'] = how
            ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]

        rows = [(cid, s) for cid, s in ranked]
        if rerank and rows:
            res, ok = self._rerank(query, rows)
            if ok and res:
                rows = [(cid, float(s)) for (cid, _old), s in res]

        out, seen_sec = [], set()
        for cid, s in rows:
            ch = self._chunk(cid)
            if ch is None:
                continue
            sec = (ch['path'], ch['heading'])
            if expand and sec in seen_sec:
                continue  # merge: one row per (page, section) on broad questions
            seen_sec.add(sec)
            text = ch['text']
            if expand:
                # pull the whole section (all its chunks) for context
                sibs = self.conn.execute(
                    'SELECT text FROM chunks WHERE path=? AND heading=? ORDER BY id',
                    (ch['path'], ch['heading'])).fetchall()
                text = '\n\n'.join(r['text'] for r in sibs)
            out.append({'path': ch['path'], 'heading': ch['heading'].strip('# ').strip(),
                        'layer': ch['layer'], 'topic': ch['topic'],
                        'score': round(float(s), 4),
                        'snippet': ' '.join(text.split())[:220],
                        'text': text})
            if len(out) >= top_k:
                break
        return out

    def route(self, query, top_masters=3):
        """Task mode (RETRIEVAL.md): which MASTER(S) should I read in full?

        Aggregates BM25 chunk scores per master file, then returns a reading
        order — hub first, sub-masters by score — with the question each
        master answers, its level and word count. The agent then reads the
        listed masters COMPLETELY before executing the task (the "expert in
        one read" doctrine of MASTER_GUIDE.md).
        """
        hits = self.search(query, top_k=50, layer='master')
        by_path = {}
        for h in hits:
            by_path.setdefault(h['path'], {'score': 0.0, 'headings': []})
            by_path[h['path']]['score'] += h['score']
            if h['heading'] and h['heading'] not in by_path[h['path']]['headings']:
                by_path[h['path']]['headings'].append(h['heading'])
        ranked = sorted(by_path.items(), key=lambda kv: -kv[1]['score'])[:top_masters]
        out = []
        for path, info in ranked:
            full = os.path.join(self.root, path)
            meta, body = split_frontmatter(
                open(full, encoding='utf-8', errors='replace').read()) \
                if os.path.isfile(full) else ({}, '')
            out.append({'path': path, 'score': round(info['score'], 3),
                        'question': str(meta.get('question', '')),
                        'master_level': str(meta.get('master_level', '')),
                        'hub': bool(meta.get('hub', False)),
                        'words': len(body.split()),
                        'matched_headings': info['headings'][:4]})
        # hub masters read before sub-masters of equal rank
        out.sort(key=lambda r: (not r['hub'], -r['score']))
        return out


def _resolve_root(argv_ns):
    """CLI helper: --namespace wins; else cwd if it is a KB; else repo root."""
    root = paths.repo_root()
    if argv_ns.namespace:
        kb = paths.find_kb(root, argv_ns.namespace)
        if kb is None:
            print('namespace %r not found (have: %s)' % (
                argv_ns.namespace,
                ', '.join(os.path.basename(d) for d in paths.kb_dirs(root)) or 'none'),
                file=sys.stderr)
            return None
        return kb
    cwd = os.getcwd()
    if os.path.isfile(os.path.join(cwd, 'config.yml')) and \
            os.path.abspath(cwd) != os.path.abspath(root):
        return cwd
    return root


def main(argv=None):
    ap = argparse.ArgumentParser(description='knowledge-forge retrieval engine')
    sub = ap.add_subparsers(dest='cmd', required=True)
    ix = sub.add_parser('index', help='(re)build the SQLite/BM25 index (incremental)')
    ix.add_argument('--force', action='store_true', help='full rebuild from scratch')
    ix.add_argument('--namespace')
    st = sub.add_parser('status', help='index statistics')
    st.add_argument('--namespace')
    s = sub.add_parser('search', help='search the knowledge base')
    s.add_argument('query')
    s.add_argument('-k', '--top-k', type=int, default=10)
    s.add_argument('--topic')
    s.add_argument('--layer', choices=sorted(set(LAYER_BY_FOLDER.values())))
    s.add_argument('--namespace')
    s.add_argument('--engine', choices=['auto', 'keyword', 'hybrid', 'dense'],
                   default='auto')
    s.add_argument('--rerank', action='store_true',
                   help='cross-encoder rerank of fused candidates')
    s.add_argument('--expand', action='store_true',
                   help='broad questions: expand hits to full sections')
    s.add_argument('--json', action='store_true')
    r = sub.add_parser('route', help='TASK mode: which master(s) to read in full')
    r.add_argument('query')
    r.add_argument('-m', '--top-masters', type=int, default=3)
    r.add_argument('--namespace')
    r.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    root = _resolve_root(args)
    if root is None:
        return 1

    if args.cmd == 'index':
        nf, nc, nnew, nunch = build_index(root, force=args.force)
        print('indexed %d files -> %d chunks (%d re-chunked, %d unchanged) (%s)' % (
            nf, nc, nnew, nunch, db_path(root)))
        return 0
    if args.cmd == 'status':
        if not os.path.isfile(db_path(root)):
            print('no index — run: python tools/retriever.py index%s' %
                  (' --namespace ' + args.namespace if args.namespace else ''))
            return 1
        c = Searcher(root)
        for r_ in c.conn.execute('SELECT * FROM meta'):
            print('%-12s %s' % (r_['key'], r_['value']))
        for r_ in c.conn.execute(
                'SELECT layer, COUNT(*) n FROM chunks GROUP BY layer ORDER BY n DESC'):
            print('%-12s %d chunks' % (r_['layer'] or '-', r_['n']))
        return 0
    if not os.path.isfile(db_path(root)):
        print('no index — run: python tools/retriever.py index first', file=sys.stderr)
        return 1
    if args.cmd == 'route':
        res = Searcher(root).route(args.query, args.top_masters)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if not res:
            print('no master matches this task — the topic may not be built yet')
            return 1
        print('TASK ROUTE — read these masters IN FULL, in this order:\n')
        for i, m in enumerate(res, 1):
            print('%d. %s  [%.1f]' % (i, m['path'], m['score']))
            if m['question']:
                print('   question: %s' % m['question'])
            bits = [b for b in ('hub' if m['hub'] else '',
                               m['master_level'],
                               '%d words' % m['words']) if b]
            if bits:
                print('   %s' % ' · '.join(bits))
            if m['matched_headings']:
                print('   matched: %s' % ', '.join(m['matched_headings'][:3]))
        print('\nthen execute the task using ONLY what these masters say,')
        print('citing sources for every claim, and saying "not in the sources"')
        print('for anything they do not cover.')
        return 0
    c = Searcher(root)
    res = c.search(args.query, args.top_k, args.topic, args.layer,
                   engine=args.engine, rerank=args.rerank, expand=args.expand)
    if args.json:
        for r_ in res:
            r_.pop('text', None)
        print(json.dumps({'engine': c.last_engine, 'results': res},
                         ensure_ascii=False, indent=2))
        return 0
    if not res:
        print('not in the sources (no chunk matched the query)')
        return 1
    print('engine: %s' % json.dumps(c.last_engine))
    for i, r_ in enumerate(res, 1):
        print('%2d. [%.3f] %s%s%s' % (i, r_['score'], r_['path'],
                                       ' · ' + r_['topic'] if r_['topic'] else '',
                                       ' · ' + r_['layer'] if r_['layer'] else ''))
        if r_['heading']:
            print('     # %s' % r_['heading'])
        print('     %s' % r_['snippet'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
