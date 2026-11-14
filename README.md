# Knowledge Forge

Turn a pile of raw documents into a knowledge base an AI can actually reason over.

Drop your files into `sources/`, tell your AI assistant **“Read `AGENT.md` and follow it”**, and it will convert your sources into a layered, cited, queryable knowledge base. When you later ask a question, the assistant answers from *your* knowledge, with a source for every claim — not from its own memory.

Works with any topic (business, law, medicine, a hobby, a company handbook) and any language. No servers, no database, no vendor lock‑in. Plain Markdown + Git. Any coding assistant that can read and write files can run it.

## Quick start

1. **Get the repo.** Clone or download it.
2. **Add your material.** Copy your documents (transcripts, notes, PDFs exported to text, articles) into `sources/`. Anything goes in, whole, unedited.
3. **Point your assistant at it.** Open your AI coding assistant in this folder and say:
   > Read `AGENT.md` and follow it to build my knowledge base from `sources/`.
4. **Ask questions.** Once it has built masters, ask things like *“Using everything here, draft me a plan for X.”* The assistant reads the masters and answers as a specialist, citing sources.

## What you get

- A clean pipeline: `source → atom → concept → tension → master`.
- **Masters**: one big file per topic that makes the model an expert in that topic in a single read.
- Every claim traceable to an exact quote in a source file.
- Conflicting views kept side by side, never silently “corrected.”

## How it reads (map)

| You want… | Open |
|---|---|
| The one instruction file for the AI | `AGENT.md` |
| The non‑negotiable rules | `docs/PRINCIPLES.md` |
| The layers and strict naming | `docs/ONTOLOGY.md` |
| Measurable quality gates | `docs/GATES.md` |
| Folder layout | `docs/STRUCTURE.md` |
| How to build a master | `docs/MASTER_GUIDE.md` |
| How concepts and atoms are written | `docs/CONCEPT_GUIDE.md` |
| How the AI answers your questions | `docs/RETRIEVAL.md` |
| How to configure it for your project | `config.yml` |

## Why it is built this way
Every rule here exists to prevent a specific, common failure of ad‑hoc “just summarize my files” attempts: summaries that drift from the source, numbers no one can verify, one big blob the model can’t navigate, and “expert” files that are confidently wrong. See `docs/PRINCIPLES.md`.

## License
MIT (see `LICENSE`). Use it, fork it, build on it.
