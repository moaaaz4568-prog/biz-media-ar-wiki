# Knowledge Forge

Turn a pile of raw documents into a knowledge base an AI can actually reason over.

Drop your files into `sources/`, tell your AI assistant **"Read `AGENT.md` and follow it"**, and it will convert your sources into a layered, cited, queryable knowledge base. When you later ask a question, the assistant answers from *your* knowledge, with a source for every claim — not from its own memory.

Works with any topic (business, law, medicine, a hobby, a company handbook) and any language. No servers, no database, no vendor lock‑in. Plain Markdown + Git. Any coding assistant that can read and write files can run it.

**The method ships with executable tools** (`tools/`, Python stdlib only for the core loop — no dependencies to install): the GATES.md checks run as code, retrieval is a real BM25 engine over a SQLite index (language-aware, Arabic first), evaluation measures recall@k per tier / faithfulness instead of asserting them, and `forge verify` turns the whole quality system into one PASS/FAIL command.

**v2 adds**: multiple **namespaces** with structural isolation (one index per knowledge base, leak-tested), **hybrid retrieval** (BM25 + local dense embeddings + RRF fusion + optional rerank — runs fully local, no API), a **running answering system** (constrained generation with answer receipts and runtime faithfulness, via CLI and MCP), **graduated evaluation tiers** (exact / paraphrase / comparison / unanswerable — reported per tier, never blended), and a second worked example in a different language and topic.

## Quick start

1. **Get the repo.** Clone or download it.
2. **Create your namespace.** `python3 tools/forge.py init mykb --language en`
   (or work in the repo root's `sources/` — the default namespace).
3. **Add your material.** Copy your documents (transcripts, notes, PDFs exported to text, articles) into `namespaces/mykb/sources/`. Anything goes in, whole, unedited.
4. **Point your assistant at it.** Open your AI coding assistant in this folder and say:
   > Read `AGENT.md` and follow it to build my knowledge base from `namespaces/mykb/sources/`.
5. **Build + verify.** `python3 tools/forge.py build --namespace mykb` runs the pipeline with gates; `python3 tools/forge.py verify` prints one PASS/FAIL over gates + tests + eval + the namespace leak test.
6. **Ask.** `python3 tools/forge.py ask "your question" --namespace mykb` — cited answer or exactly "not in the sources".

## See it working before you start

Two complete examples ship in the repo — **different languages, different topics, both green** (the generality proof: a change breaking either fails):

```bash
python3 tools/forge.py verify                       # gates + self-test + tests + eval + leak test
python3 tools/forge.py status                       # what is built, per namespace

cd examples/ar-outreach                             # Arabic cold-email workshop KB
python3 ../../tools/gates.py check                  # 16 entities, 0 rejected (repo-wide)
python3 ../../tools/retriever.py search "ما سقف عدد الكلمات في الرسالة"
python3 ../../tools/retriever.py route "اعمل حملة أوتريتش جديدة"    # TASK mode

cd ../en-handbook                                   # English café ops handbook KB
python3 ../../tools/forge.py ask "How long do espresso machines need to warm up?" --namespace en-handbook
```

**Optional dense rung** (fully local, ~118 MB, no API keys):
```bash
pip install onnxruntime tokenizers sqlite-vec
python3 tools/embed.py download e5-small
python3 tools/embed.py index --namespace ar-outreach
python3 tools/evalrun.py --compare-engines         # keyword vs hybrid, per tier
```
Without them everything above still works — keyword-only, and the answer receipt says so.

## What you get

- A clean pipeline: `source → glossary → atom → concept → tension → master`, enforced by **executable gates** (`tools/gates.py` — C1–C8 / M1–M10 / T1–T4 / X1–X4 / G1–G2 / N1, 26 gates with a self-test proving each can fail).
- **Namespaces** (`tools/forge.py init`): one corpus, one voice, one index each — isolation proven by canary leak tests, not asserted (see `docs/NAMESPACES.md`).
- **Graduated master levels** (L0→L3): your first master starts at 6 sections / 2,000 words and climbs to 18 / 10,000 as the topic matures — instead of being rejected on day one.
- **A real retrieval engine** (`tools/retriever.py`): BM25 over language-normalized tokens (per-language registry — Arabic folding built in, English stemming, add more as data), hybrid fusion with local ONNX embeddings, SQLite-backed, incremental by content hash, topic/layer/namespace filters.
- **A running answering system**: `forge ask` (QUESTION), `forge do` (TASK — reads the routed masters in full, then executes from them), the MCP server for any MCP-capable model, answer receipts, runtime faithfulness, and the "not in the sources" contract (see `docs/ANSWERING.md`).
- **Measurement, not assertion** (`tools/evalrun.py`): recall@k per tier (exact / paraphrase / comparison / unanswerable) against known-answer questions, `--compare-engines` for keyword vs hybrid, faithfulness of generated answers — separated from generation, as the method requires.
- Every claim traceable to an exact quote in a source file (the gates verify quotes against `sources/`, line-wrap folded).
- Conflicting views kept side by side, never silently "corrected."

## How it reads (map)

| You want… | Open |
|---|---|
| The one instruction file for the AI | `AGENT.md` |
| The non‑negotiable rules | `docs/PRINCIPLES.md` |
| The layers and strict naming | `docs/ONTOLOGY.md` |
| Measurable quality gates (and the tool that runs them) | `docs/GATES.md` + `tools/gates.py` |
| Namespaces and isolation | `docs/NAMESPACES.md` |
| How the AI answers (modes, receipts, rungs) | `docs/ANSWERING.md` |
| Folder layout | `docs/STRUCTURE.md` |
| How to build a master | `docs/MASTER_GUIDE.md` |
| How concepts and atoms are written | `docs/CONCEPT_GUIDE.md` |
| How the search engine works (and the tools behind it) | `docs/RETRIEVAL.md` + `tools/retriever.py` + `tools/embed.py` |
| How to configure it for your project | `config.yml` |
| How evaluation is measured | `tools/evalrun.py` + `eval/questions.yml` (tiers) |
| Complete worked examples (AR + EN) | `examples/ar-outreach/`, `examples/en-handbook/` |
| Every decision with its rejected alternative | `DECISIONS.md` (D1–D20) |
| What was measured, with commands | `LOG.md` |

## Why it is built this way
Every rule here exists to prevent a specific, common failure of ad‑hoc "just summarize my files" attempts: summaries that drift from the source, numbers no one can verify, one big blob the model can't navigate, and "expert" files that are confidently wrong. See `docs/PRINCIPLES.md`.

The tools follow the same doctrine: gates are code (a gate that can't fail is broken — so each one is tested with a known-bad case), retrieval is measured before trusted (the paraphrase tier exists because keyword-only measurably collapses on it: 0.750 → hybrid 1.000 on the Arabic example), and the core loop runs on the Python standard library alone — dense embeddings and the answering LLM are optional, declared, degradable rungs, and the system always says which rung it is on.

## License
MIT (see `LICENSE`). Use it, fork it, build on it.
