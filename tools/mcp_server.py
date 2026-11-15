#!/usr/bin/env python3
"""mcp_server.py — the machine door (v2 §8.2).

A thin stdio JSON-RPC server over the SAME engine the CLI uses: same
retrieval, same gates philosophy, same receipts. One engine, two doors —
never two engines that drift apart.

The server NEVER edits the knowledge base: search/answer/route are all
read-only. Writing goes through the CLI pipeline with gates (§8.2), so
no model gets a write path that bypasses them.

Protocol (JSON-RPC 2.0 over stdin/stdout, one request per line):
    {"jsonrpc":"2.0","id":1,"method":"tools/list"}
    {"jsonrpc":"2.0","id":2,"method":"tools/call",
     "params":{"name":"search","arguments":{"namespace":"en-handbook",
                                            "query":"shot clock","top_k":5}}}

Tools:
    search(namespace, query, top_k) -> passages + paths + headings
    answer(namespace, query)        -> constrained answer + citations + receipt
    route(task, namespace)          -> reading order (hub first)

Run:  python tools/mcp_server.py          (from the repo root)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kforge import paths, receipts, faith  # noqa: E402

TOOLS = [
    {
        'name': 'search',
        'description': 'Search one namespace. Returns ranked passages with '
                       'file paths, headings, layers and scores. Read-only.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'namespace': {'type': 'string',
                              'description': 'namespace id (folder name under '
                                             'namespaces/ or examples/)'},
                'query': {'type': 'string'},
                'top_k': {'type': 'integer', 'default': 8},
                'layer': {'type': 'string', 'enum': ['source', 'atom', 'concept',
                                                     'tension', 'glossary',
                                                     'master', 'synthesis']},
            },
            'required': ['namespace', 'query'],
        },
    },
    {
        'name': 'answer',
        'description': 'Constrained answer from one namespace: every sentence '
                       'backed by a retrieved passage, citations included, '
                       'answer receipt attached. "not in the sources" when no '
                       'passage matches. Read-only.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'namespace': {'type': 'string'},
                'query': {'type': 'string'},
                'top_k': {'type': 'integer', 'default': 8},
            },
            'required': ['namespace', 'query'],
        },
    },
    {
        'name': 'route',
        'description': 'TASK mode: which master(s) to read IN FULL and in '
                       'what order (hub first), with each master\'s question, '
                       'level and size. Read-only.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'namespace': {'type': 'string'},
                'task': {'type': 'string'},
                'top_masters': {'type': 'integer', 'default': 3},
            },
            'required': ['namespace', 'task'],
        },
    },
]

SYSTEM_QUESTION = """You answer ONLY from the retrieved passages provided.
Rules:
- Every sentence must be backed by a passage; cite file paths inline like [sources/S_x.md].
- If the passages do not contain the answer, reply exactly: not in the sources
- Show both sides when passages conflict (tensions).
- Answer in the language of the question.
- Never use your training knowledge to fill gaps."""


def _err(msg):
    print(json.dumps({'error': {'code': -32000, 'message': msg}}),
          flush=True)


def _find_kb(namespace):
    root = paths.repo_root()
    kb = paths.find_kb(root, namespace)
    if kb is None:
        return None
    return kb


def tool_search(args):
    import retriever as R
    kb = _find_kb(args['namespace'])
    if kb is None:
        return {'error': 'unknown namespace %r' % args['namespace']}
    s = R.Searcher(kb)
    hits = s.search(args['query'], top_k=args.get('top_k', 8),
                    layer=args.get('layer'), engine='auto')
    canary_free = [p for p in hits
                   if not p['path'].startswith('sources/CANARY-')]
    return {'engine': s.last_engine,
            'results': [{'path': p['path'], 'heading': p['heading'],
                         'layer': p['layer'], 'topic': p['topic'],
                         'score': p['score'], 'snippet': p['snippet']}
                        for p in canary_free]}


def tool_answer(args):
    import retriever as R
    kb = _find_kb(args['namespace'])
    if kb is None:
        return {'error': 'unknown namespace %r' % args['namespace']}
    ns = paths.ns_name(kb)
    s = R.Searcher(kb)
    passages = s.search(args['query'], top_k=args.get('top_k', 8),
                        engine='auto', expand=True)
    passages = [p for p in passages
                if not p['path'].startswith('sources/CANARY-')]
    if not passages:
        r = receipts.build(ns, args['query'], 'QUESTION',
                           dict(retrieval=s.last_engine.get('retrieval'),
                                dense=s.last_engine.get('dense'),
                                fusion=s.last_engine.get('fusion'),
                                rerank=s.last_engine.get('rerank'),
                                llm=None),
                           [], 'not in the sources')
        return {'answer': 'not in the sources', 'receipt': r}

    corpus = '\n\n'.join('[%d] %s # %s\n%s' % (
        i + 1, p['path'], p['heading'], p['text'])
        for i, p in enumerate(passages))
    user = ('QUESTION: %s\n\nPASSAGES:\n%s\n\nAnswer ONLY from the passages, '
            'cite paths.' % (args['query'], corpus))
    from kforge import llm
    try:
        out = llm.chat(SYSTEM_QUESTION, user)
    except llm.LLMUnavailable as e:
        # degradation rung (idea 14): passages + citations, no prose, and SAY so
        return {'answer': None,
                'degraded': 'retrieval-only (LLM unavailable: %s)' % e,
                'passages': [{'path': p['path'], 'heading': p['heading'],
                              'snippet': p['snippet']} for p in passages],
                'engine': s.last_engine}
    answer = out['content']
    share, total, backed, unbacked = faith.backed_share(answer, corpus)
    r = receipts.build(
        ns, args['query'], 'QUESTION',
        dict(retrieval=s.last_engine.get('retrieval'),
             dense=s.last_engine.get('dense'),
             fusion=s.last_engine.get('fusion'),
             rerank=s.last_engine.get('rerank'),
             llm=out.get('model')),
        passages, answer,
        faith={'backed': backed, 'total': total,
               'ok': share is None or share >= 0.9,
               'share': round(share, 3) if share is not None else None},
        llm=out)
    return {'answer': answer, 'receipt': r}


def tool_route(args):
    import retriever as R
    kb = _find_kb(args['namespace'])
    if kb is None:
        return {'error': 'unknown namespace %r' % args['namespace']}
    s = R.Searcher(kb)
    routed = s.route(args['task'], top_masters=args.get('top_masters', 3))
    if not routed:
        return {'routed': [],
                'note': 'no master matches this task — the topic may not be '
                        'built yet; propose building it (sources -> atoms -> '
                        'concepts -> master) instead of improvising'}
    return {'routed': routed,
            'note': 'read every listed master IN FULL before executing'}


HANDLERS = {'search': tool_search, 'answer': tool_answer, 'route': tool_route}


def handle(req):
    mid = req.get('id')
    method = req.get('method')
    if method == 'initialize':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {
            'protocolVersion': '2024-11-05',
            'capabilities': {'tools': {}},
            'serverInfo': {'name': 'knowledge-forge', 'version': '2.0.0'}}}
    if method == 'notifications/initialized':
        return None  # notification — no response
    if method == 'tools/list':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {'tools': TOOLS}}
    if method == 'tools/call':
        params = req.get('params') or {}
        name = params.get('name')
        if name not in HANDLERS:
            return {'jsonrpc': '2.0', 'id': mid,
                    'error': {'code': -32601, 'message': 'unknown tool %r' % name}}
        try:
            result = HANDLERS[name](params.get('arguments') or {})
        except Exception as e:
            return {'jsonrpc': '2.0', 'id': mid,
                    'error': {'code': -32000, 'message': '%s: %s' % (
                        type(e).__name__, e)}}
        return {'jsonrpc': '2.0', 'id': mid, 'result': {
            'content': [{'type': 'text',
                         'text': json.dumps(result, ensure_ascii=False)}]}}
    if method == 'ping':
        return {'jsonrpc': '2.0', 'id': mid, 'result': {}}
    return {'jsonrpc': '2.0', 'id': mid,
            'error': {'code': -32601, 'message': 'unknown method %r' % method}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            _err('bad json: %s' % e)
            continue
        resp = handle(req)
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
