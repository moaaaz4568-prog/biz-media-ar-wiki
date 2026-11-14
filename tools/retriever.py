#!/usr/bin/env python3
"""retriever.py — a real retrieval engine for the knowledge base (fix for gap #2).

RETRIEVAL.md assumed the model "reads INDEX.md and greps". That fails at
scale. This tool builds a SQLite index over every layer (sources, atoms,
concepts, tensions, glossary, masters) and answers queries with BM25 over
Arabic-normalized tokens — stdlib only (D7: keyword first, no dependencies).

The index is derived data, so it lives in .kforge/ (gitignored) and can be
rebuilt at any time:  python tools/retriever.py index

Usage (from knowledge-forge/ root):
    python tools/retriever.py index                 # (re)build the index
    python tools/retriever.py search "سؤالك"        # top-10 chunks, BM25
    python tools/retriever.py search "query" -k 5 --topic outreach --layer concept
    python tools/retriever.py status                # index stats
"""

import argparse
import json
import math
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge.arabic import tokenize  # noqa: E402
from kforge.frontmatter import split_frontmatter  # noqa: E402

DB_DIR = '.kforge'
CHUNK_WORDS = 400          # max words per chunk (sections split beyond this)
MIN_TOKENS_FOR_MATCH = 1   # a chunk must share at least this many query tokens

LAYER_BY_FOLDER = {
    'sources': 'source', 'atoms': 'atom', 'concepts': 'concept',
    'tensions': 'tension', 'glossary': 'glossary', 'masters': 'master',
    'synthesis': 'synthesis',
}
_HEADING_RE = re.compile(r'^#{1,4}\s+(.*?)\s*$', re.M)


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


def build_index(root):
    os.makedirs(os.path.join(root, DB_DIR), exist_ok=True)
    conn = sqlite3.connect(db_path(root))
    conn.executescript("""
    DROP TABLE IF EXISTS chunks; DROP TABLE IF EXISTS postings; DROP TABLE IF EXISTS meta;
    CREATE TABLE chunks(id INTEGER PRIMARY KEY, path TEXT, heading TEXT, layer TEXT,
                        topic TEXT, nwords INTEGER, text TEXT);
    CREATE TABLE postings(term TEXT, chunk_id INTEGER, tf INTEGER);
    CREATE TABLE meta(key TEXT PRIMARY KEY, value INTEGER, extra TEXT);
    CREATE INDEX idx_postings_term ON postings(term);
    CREATE INDEX idx_chunks_path ON chunks(path);
    """)
    n_files, n_chunks = 0, 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in
                   ('.git', DB_DIR, 'archive', 'rejected', 'node_modules', 'tools', 'docs', 'eval', 'examples')]
        for fn in sorted(files):
            if not fn.endswith('.md') or fn in ('INDEX.md', 'LOG.md'):
                continue
            p = os.path.join(dirpath, fn)
            n_files += 1
            raw = open(p, encoding='utf-8', errors='replace').read()
            _meta, body = split_frontmatter(raw)
            layer, topic, rel = _layer_topic(root, p)
            for heading, sec in _sections(body):
                for h, piece in _chunks(heading, sec):
                    toks = tokenize(piece)
                    if not toks:
                        continue
                    cur = conn.execute(
                        'INSERT INTO chunks(path,heading,layer,topic,nwords,text) VALUES(?,?,?,?,?,?)',
                        (rel, heading, layer, topic, len(piece.split()), piece))
                    counts = {}
                    for t in toks:
                        counts[t] = counts.get(t, 0) + 1
                    conn.executemany('INSERT INTO postings VALUES(?,?,?)',
                                     [(t, cur.lastrowid, c) for t, c in counts.items()])
                    n_chunks += 1
    conn.executemany('INSERT INTO meta VALUES(?,?,?)',
                     [('files', n_files, ''), ('chunks', n_chunks, ''),
                      ('total_words', conn.execute(
                          'SELECT SUM(nwords) FROM chunks').fetchone()[0] or 0, '')])
    conn.commit()
    conn.close()
    return n_files, n_chunks


class Searcher:
    def __init__(self, root):
        self.root = root
        self.conn = sqlite3.connect(db_path(root))
        self.conn.row_factory = sqlite3.Row
        m = dict((r['key'], r['value']) for r in self.conn.execute('SELECT * FROM meta'))
        self.N = m.get('chunks', 0)
        self.avgdl = (m.get('total_words', 0) / self.N) if self.N else 0

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

    def search(self, query, top_k=10, topic=None, layer=None):
        """BM25 (k1=1.5, b=0.75) over normalized tokens. Returns ranked rows."""
        toks = tokenize(query)
        if not toks or not self.N:
            return []
        q = 'SELECT p.term, p.chunk_id, p.tf FROM postings p WHERE p.term IN (%s)' % \
            ','.join('?' * len(toks))
        rows = self.conn.execute(q, toks).fetchall()
        by_chunk = {}
        df = {}
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
        top = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        out = []
        for cid, s in top:
            ch = self.conn.execute('SELECT * FROM chunks WHERE id=?', (cid,)).fetchone()
            out.append({'path': ch['path'], 'heading': ch['heading'].strip('# ').strip(),
                        'layer': ch['layer'], 'topic': ch['topic'],
                        'score': round(s, 3), 'snippet': ' '.join(ch['text'].split())[:220]})
        return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='knowledge-forge retrieval engine')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('index', help='(re)build the SQLite/BM25 index')
    sub.add_parser('status', help='index statistics')
    s = sub.add_parser('search', help='BM25 search over the knowledge base')
    s.add_argument('query')
    s.add_argument('-k', '--top-k', type=int, default=10)
    s.add_argument('--topic')
    s.add_argument('--layer', choices=sorted(set(LAYER_BY_FOLDER.values())))
    s.add_argument('--json', action='store_true')
    r = sub.add_parser('route', help='TASK mode: which master(s) to read in full')
    r.add_argument('query')
    r.add_argument('-m', '--top-masters', type=int, default=3)
    r.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    root = os.getcwd()

    if args.cmd == 'index':
        nf, nc = build_index(root)
        print('indexed %d files -> %d chunks (%s)' % (nf, nc, db_path(root)))
        return 0
    if args.cmd == 'status':
        if not os.path.isfile(db_path(root)):
            print('no index — run: python tools/retriever.py index')
            return 1
        c = Searcher(root)
        for r in c.conn.execute('SELECT * FROM meta'):
            print('%-12s %s' % (r['key'], r['value']))
        for r in c.conn.execute(
                'SELECT layer, COUNT(*) n FROM chunks GROUP BY layer ORDER BY n DESC'):
            print('%-12s %d chunks' % (r['layer'] or '-', r['n']))
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
    res = Searcher(root).search(args.query, args.top_k, args.topic, args.layer)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    if not res:
        print('not in the sources (no chunk matched the query tokens)')
        return 1
    for i, r in enumerate(res, 1):
        print('%2d. [%.3f] %s%s%s' % (i, r['score'], r['path'],
                                       ' · ' + r['topic'] if r['topic'] else '',
                                       ' · ' + r['layer'] if r['layer'] else ''))
        if r['heading']:
            print('     # %s' % r['heading'])
        print('     %s' % r['snippet'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
