# Answering

> The model answers ONLY from retrieved passages. A sentence with no backing passage is dropped or marked unsupported.

## The one rule above all

Constrained generation (§5 of the v2 design): every sentence of an
answer is backed by a retrieved passage and cited with its file path.
A sentence with no backing is rejected or flagged — never shipped
silently.

- No suitable passage → the answer is exactly: **not in the sources**
  (this path is exercised by every eval set's `unanswerable` tier, and
  a hallucinated answer on those questions fails the build).
- Never answer from training memory. Never fill a gap with general
  knowledge and present it as sourced.
- Answer in the language of the question. Citations always point to
  the source file as stored.

## The four modes

| Mode | Question shape | Path |
|---|---|---|
| QUESTION | "what is the word limit?" | search → cite passages → constrained answer |
| TASK | "draft me a campaign" | `route` → read the returned masters IN FULL → execute from that expertise alone |
| COMPARISON | "X vs Y" | one search per side, both answers shown, each with its own citations |
| RELATIONAL | "who/why links" | the entity graph (`forge graph`); when not built, says so — never faked from flat retrieval |

TASK mode is where the masters' promise is cashed in: reading a master
once makes the model fluent in the topic. If `route` returns nothing,
the topic is not built yet — say so and propose building it (sources →
atoms → concepts → master) instead of improvising.

## Voice

One system prompt per namespace (from that namespace's config/voice)
+ retrieval restricted to that namespace's index + the constraint above.
All three together are what "thinking like the namespace" means — it is
not an automatic property of RAG.

## Answer receipts (every answer carries one)

```
--- answer receipt ---
namespace : ar-outreach   mode: QUESTION   2026-11-15T19:21:30+0000
engine    : retrieval=hybrid dense=e5-small fusion=rrf rerank=None llm=glm-4-plus
passages  :  1. masters/... (heading)  2. sources/...  ...
faithful  : 2/2 sentences backed
latency   : 2216 ms   tokens: {...}
receipt id: 20261115-192130-...
```

Receipts make answers reproducible and misses debuggable — a miss
without a receipt cannot be fixed. They are saved under
`<kb>/.kforge/receipts/` (generated, gitignored).

## Faithfulness — measured AND enforced at runtime

- Offline: `evalrun.py --answer answers.md` scores a supplied answer
  file (target ≥ 0.9). The tool never generates.
- Runtime: `forge ask` and the MCP `answer` tool score the generated
  answer against the retrieved passages immediately, and print the
  unbacked sentences when below threshold. The measurement stays
  separate from generation: `kforge/faith.py` only scores.

## The degradation ladder (never silent)

| Rung | What runs | What the receipt says |
|---|---|---|
| Full | hybrid retrieval + LLM constrained answer | `llm=<model>` |
| Dense off | keyword BM25 (+ wider top-N) | `dense=None` |
| LLM off | retrieval-only: passages + citations, no prose | `llm=none (retrieval-only rung)` |

The system always states which rung it is on (idea 14). Dense
embedding is optional: `pip install onnxruntime tokenizers sqlite-vec`
+ `python tools/embed.py download e5-small` turn it on; without them
the core loop (gates + keyword retrieval + eval) runs on stdlib alone.

## Commands

```bash
python3 tools/forge.py ask "question" --namespace <n>     # QUESTION mode
python3 tools/forge.py do "task" --namespace <n>          # TASK mode
python3 tools/forge.py ask "q" --namespace <n> --no-llm   # retrieval-only rung
python3 tools/forge.py graph --namespace <n> --neighbors <node>   # RELATIONAL
```
