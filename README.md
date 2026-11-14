# Knowledge Forge

Turn a pile of raw documents into a knowledge base an AI can actually reason over.

Drop your files into `sources/`, tell your AI assistant **"Read `AGENT.md` and follow it"**, and it will convert your sources into a layered, cited, queryable knowledge base. When you later ask a question, the assistant answers from *your* knowledge, with a source for every claim — not from its own memory.

Works with any topic (business, law, medicine, a hobby, a company handbook) and any language. No servers, no database, no vendor lock‑in. Plain Markdown + Git. Any coding assistant that can read and write files can run it.

**The method ships with executable tools** (`tools/`, Python stdlib only — no dependencies to install): the GATES.md checks run as code, retrieval is a real BM25 engine over a SQLite index (Arabic-aware), and evaluation measures recall@k / faithfulness instead of asserting them.

## Quick start

1. **Get the repo.** Clone or download it.
2. **Add your material.** Copy your documents (transcripts, notes, PDFs exported to text, articles) into `sources/`. Anything goes in, whole, unedited.
3. **Point your assistant at it.** Open your AI coding assistant in this folder and say:
   > Read `AGENT.md` and follow it to build my knowledge base from `sources/`.
4. **Ask questions.** Once it has built masters, ask things like *"Using everything here, draft me a plan for X."* The assistant reads the masters and answers as a specialist, citing sources.

## See it working before you start

`examples/ar-outreach/` is a complete Arabic knowledge base (source → atoms → concepts → tension → L0 master) that passes every gate and measures `recall@10 = 1.000` on 8 known-answer questions:

```bash
cd examples/ar-outreach
python3 ../../tools/gates.py check                 # all entities pass their gates
python3 ../../tools/gates.py self-test             # D8: every gate can fail (16/16)
python3 ../../tools/retriever.py index             # build the BM25 index
python3 ../../tools/retriever.py search "ما سقف عدد الكلمات في الرسالة"
python3 ../../tools/evalrun.py -k 10               # recall@10 measurement
```

## What you get

- A clean pipeline: `source → atom → concept → tension → master`, enforced by **executable gates** (`tools/gates.py` — C1–C8 / M1–M8, with a self-test proving each gate can fail).
- **Graduated master levels** (L0→L3): your first master starts at 6 sections / 2,000 words and climbs to 18 / 10,000 as the topic matures — instead of being rejected on day one.
- **A real retrieval engine** (`tools/retriever.py`): BM25 over Arabic-normalized tokens, SQLite-backed, topic/layer filters, no dependencies.
- **Measurement, not assertion** (`tools/evalrun.py`): recall@k against known-answer questions, and faithfulness of generated answers — separated from generation, as the method requires.
- Every claim traceable to an exact quote in a source file (the gates verify quotes are byte-exact against `sources/`).
- Conflicting views kept side by side, never silently "corrected."

## How it reads (map)

| You want… | Open |
|---|---|
| The one instruction file for the AI | `AGENT.md` |
| The non‑negotiable rules | `docs/PRINCIPLES.md` |
| The layers and strict naming | `docs/ONTOLOGY.md` |
| Measurable quality gates (and the tool that runs them) | `docs/GATES.md` + `tools/gates.py` |
| Folder layout | `docs/STRUCTURE.md` |
| How to build a master | `docs/MASTER_GUIDE.md` |
| How concepts and atoms are written | `docs/CONCEPT_GUIDE.md` |
| How the AI answers your questions (and the search engine behind it) | `docs/RETRIEVAL.md` + `tools/retriever.py` |
| How to configure it for your project | `config.yml` |
| How evaluation is measured | `tools/evalrun.py` + `eval/questions.yml` |
| A complete worked example | `examples/ar-outreach/` |

## Why it is built this way
Every rule here exists to prevent a specific, common failure of ad‑hoc "just summarize my files" attempts: summaries that drift from the source, numbers no one can verify, one big blob the model can't navigate, and "expert" files that are confidently wrong. See `docs/PRINCIPLES.md`.

The tools follow the same doctrine: gates are code (a gate that can't fail is broken — so each one is tested with a known-bad case), retrieval is measured before trusted, and the whole system runs on the Python standard library alone.

## License
MIT (see `LICENSE`). Use it, fork it, build on it.
