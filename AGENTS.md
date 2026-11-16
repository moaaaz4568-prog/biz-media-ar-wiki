# AGENTS.md — machine-readable summary for coding agents

This repo is **Knowledge Forge**: a methodology template that turns raw
documents in `sources/` into a layered, cited, queryable knowledge base.
The full instructions live in `AGENT.md` (read it before doing any
knowledge work). This file tells agents what the tooling is and how to
run it.

## Non-negotiable rules (details in docs/PRINCIPLES.md)
- Never edit anything under `sources/` — read-only witnesses.
- No claim without a verbatim, byte-exact quote from a source.
- Never delete: move to `archive/` (with a dated reason) or `rejected/`.
- Conflicts are kept as tensions (`X_`), never silently resolved.
- One prefix + one folder + one `type:` per entity (triple match).
- Build order: glossary FIRST, then atoms, concepts, tensions, masters (§3).
- Never mix namespaces: search/answer inside one namespace; cross-namespace
  only via a declared `Y_` synthesis (docs/NAMESPACES.md).

## Tools

**Core loop (Python stdlib only — no pip installs):**

| Command | What it does |
|---|---|
| `python3 tools/forge.py verify` | One PASS/FAIL: gates self-test + check + unit tests + per-namespace eval + leak test |
| `python3 tools/forge.py init <name> [--language en]` | Scaffold a namespace (folders, config, canary, eval skeleton) |
| `python3 tools/forge.py build --namespace <n>` | Run the pipeline with gates; stops naming the failing file |
| `python3 tools/forge.py status` | What is built per namespace (layers, chunks, vectors) |
| `python3 tools/gates.py check [--namespace <n>]` | Run all gates (C/M/T/X/G/N) over every entity |
| `python3 tools/gates.py self-test` | D8: prove every gate can fail on known-bad input (26 gates) |
| `python3 tools/retriever.py index [--force] [--namespace <n>]` | (Re)build the BM25/SQLite index — incremental by content hash |
| `python3 tools/retriever.py search "query" -k 10 [--namespace <n>] [--layer concept] [--engine hybrid]` | Retrieve passages (language-normalized; hybrid when dense is on) |
| `python3 tools/retriever.py route "task" -m 3 [--namespace <n>]` | TASK mode: which master(s) to read in full, in what order |
| `python3 tools/forge.py ask "q" --namespace <n>` | QUESTION mode: cited answer + receipt, or exactly "not in the sources" |
| `python3 tools/forge.py do "task" --namespace <n>` | TASK mode: routes masters, reads them in full, executes |
| `python3 tools/forge.py graph [--namespace <n>] [--neighbors <node>]` | Entity graph from wiki-links (RELATIONAL questions) |
| `python3 tools/forge.py radar [--namespace <n>]` | Contradiction radar: PROPOSES X_ drafts (a human confirms) |
| `python3 tools/evalrun.py -k 10 [--namespace <n>]` | recall@k PER TIER (exact/paraphrase/comparison/unanswerable) |
| `python3 tools/evalrun.py --compare-engines [--namespace <n>]` | keyword vs hybrid on the same questions |
| `python3 tools/mcp_server.py` | MCP stdio server: tools search/answer/route (read-only) |

**Optional rungs (declared, degradable — the system says when it is on them):**

| Command | What it does |
|---|---|
| `python3 tools/embed.py info` | What is available locally (models, onnx stack, sqlite-vec) |
| `python3 tools/embed.py download e5-small` | Fetch the local embedding model (~118 MB, int8 ONNX) |
| `python3 tools/embed.py index --namespace <n>` | Sync the dense vector store (`.kforge/vec.db`) to the BM25 index |

Requirements for the dense rung: `pip install onnxruntime tokenizers sqlite-vec`.
Without them: keyword-only, receipts say `dense=None`. The LLM rung uses the
`z-ai` CLI when present; without it `ask` degrades to retrieval-only and says so.

## Working rules for agents
- After creating/editing any concept, atom, tension, glossary entry or master,
  run its gate; REJECTED means fix the file.
- After any bulk change: rebuild the index (`retriever.py index`), then the
  dense store if the namespace uses it (`embed.py index`), then measure.
- For a TASK ("اعملي بزنس بلان", "build me X"): `route` first, then read the
  returned masters IN FULL before executing — that is the whole point of masters.
- Answer questions only from retrieved passages; cite the source file per
  claim; say "not in the sources" when there is no evidence.
- Never expand a namespace's base before its known-answer eval passes.
- Add every measured result to `LOG.md` with the exact command that produced it.
- Every behavior change adds a `DECISIONS.md` row (decision + rejected
  alternative + reason).
- Two worked examples live in `examples/ar-outreach/` (Arabic) and
  `examples/en-handbook/` (English) — a change breaking either fails.
