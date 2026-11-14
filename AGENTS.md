# AGENTS.md — machine-readable summary for coding agents

This repo is **Knowledge Forge**: a methodology template that turns raw
documents in `sources/` into a layered, cited knowledge base. The full
instructions live in `AGENT.md` (read it before doing any knowledge work).
This file tells agents what the tooling is and how to run it.

## Non-negotiable rules (details in docs/PRINCIPLES.md)
- Never edit anything under `sources/` — read-only witnesses.
- No claim without a verbatim, byte-exact quote from a source.
- Never delete: move to `archive/` (with a dated reason) or `rejected/`.
- Conflicts are kept as tensions (`X_`), never silently resolved.
- One prefix + one folder + one `type:` per entity (triple match).

## Tools (Python stdlib only — no pip installs)

| Command | What it does |
|---|---|
| `python3 tools/gates.py check` | Run all C/M gates over every concept and master |
| `python3 tools/gates.py concept <file>` / `master <file>` | Gate one entity (exit 1 = REJECTED) |
| `python3 tools/gates.py self-test` | D8: prove every gate can fail on known-bad input |
| `python3 tools/retriever.py index` | (Re)build the BM25/SQLite index in `.kforge/` |
| `python3 tools/retriever.py search "query" -k 10 [--topic T] [--layer concept]` | Retrieve passages (Arabic-normalized) |
| `python3 tools/retriever.py route "task" -m 3` | TASK mode: which master(s) to read in full, in what order |
| `python3 tools/evalrun.py -k 10 [--answer answers.md]` | Measure recall@k (+ faithfulness) vs `eval/questions.yml` |

## Working rules for agents
- After creating/editing any concept or master, run its gate; REJECTED means fix the file.
- For a TASK ("اعملي بزنس بلان", "build me X"): `route` first, then read the returned masters IN FULL before executing — that is the whole point of masters.
- Answer questions only from retrieved passages; cite the source file per claim; say "not in the sources" when there is no evidence.
- Rebuild the index after any bulk change before measuring.
- Add every measured result to `LOG.md` with the exact command that produced it.
- A worked example lives in `examples/ar-outreach/` — run the commands there to see expected output.
