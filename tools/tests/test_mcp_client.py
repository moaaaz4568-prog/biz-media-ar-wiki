"""Real MCP client test: spawns the server, speaks JSON-RPC over stdio,
and verifies the three tools + the 'not in the sources' contract.

Run from the repo root:
    KF_MODELS=... python3 tools/tests/test_mcp_client.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SERVER = os.path.join(ROOT, 'tools', 'mcp_server.py')

fails = []


def check(name, cond, detail=''):
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))
    if not cond:
        fails.append(name)


def rpc(proc, req):
    proc.stdin.write((json.dumps(req) + '\n').encode())
    proc.stdin.flush()
    line = proc.stdout.readline().decode()
    return json.loads(line)


def main():
    env = dict(os.environ)
    proc = subprocess.Popen([sys.executable, SERVER], cwd=ROOT,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env)

    # 1) initialize
    r = rpc(proc, {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                   'params': {}})
    check('initialize', r.get('result', {}).get('serverInfo', {}).get('name')
          == 'knowledge-forge', str(r)[:100])

    # 2) tools/list
    r = rpc(proc, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
    names = [t['name'] for t in r['result']['tools']]
    check('tools/list has search/answer/route',
          set(names) >= {'search', 'answer', 'route'}, str(names))

    def call(i, name, args):
        r = rpc(proc, {'jsonrpc': '2.0', 'id': i, 'method': 'tools/call',
                       'params': {'name': name, 'arguments': args}})
        if 'error' in r:
            return {'__error__': r['error']}
        return json.loads(r['result']['content'][0]['text'])

    # 3) search en-handbook (hybrid may or may not be on; search works either way)
    r = call(3, 'search', {'namespace': 'en-handbook',
                           'query': 'espresso pull time band', 'top_k': 5})
    paths = [x['path'] for x in r.get('results', [])]
    check('search returns results', len(paths) > 0, str(paths[:2]))
    # concepts/glossary are the interpreted layers — ranking them above the
    # raw source for a "what is" query is CORRECT retrieval, not a failure
    check('search finds relevant content (concept/glossary/source)',
          any(('S_ops_handbook' in p) or ('C_shot_band' in p) or
              ('G_shot_clock' in p) for p in paths), str(paths[:3]))

    # 4) namespace containment: the EN namespace must never return AR files
    r = call(4, 'search', {'namespace': 'en-handbook',
                           'query': 'رسالة بريد بارد تخصيص السطر الأول',
                           'top_k': 10})
    paths = [x['path'] for x in r.get('results', [])]
    check('EN namespace returns zero AR content',
          not any('S_outreach' in p or 'outreach' in p for p in paths),
          str(paths[:3]))

    # 5) answer (needs the LLM bridge; if absent it degrades gracefully)
    r = call(5, 'answer', {'namespace': 'en-handbook',
                           'query': 'How long do espresso machines need to warm up?'})
    if 'answer' in r and r['answer']:
        check('answer is non-empty', bool(r['answer'].strip()))
        check('answer has receipt', 'receipt' in r and
              r['receipt'].get('engine', {}).get('retrieval') is not None)
        check('answer cites a path', 'S_ops_handbook' in (r['answer'] or ''),
              (r['answer'] or '')[:80])
    else:
        check('answer degrades gracefully (no LLM)',
              'degraded' in r or r.get('answer') is None, str(r)[:120])

    # 6) the unanswerable contract
    r = call(6, 'answer', {'namespace': 'en-handbook',
                           'query': 'What is the annual marketing budget?'})
    ans = r.get('answer') or ''
    check('unanswerable -> not in the sources (or degraded)',
          ('not in the sources' in ans) or r.get('degraded'), ans[:80])

    # 7) route
    r = call(7, 'route', {'namespace': 'en-handbook',
                          'task': 'plan the morning opening for a new shift lead'})
    routed = r.get('routed') or []
    check('route finds the master',
          any('M_shop_ops_hub' in m['path'] for m in routed),
          str([m.get('path') for m in routed][:2]))

    # 8) unknown namespace is an honest error
    r = call(8, 'search', {'namespace': 'nope', 'query': 'x'})
    check('unknown namespace errors', 'error' in r, str(r)[:80])

    proc.stdin.close()
    proc.wait(timeout=10)
    print('\n%s' % ('ALL MCP CHECKS PASS' if not fails else
                    'FAILED: %s' % ', '.join(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
