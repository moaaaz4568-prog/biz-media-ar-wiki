# Retrieval — how the AI answers questions

The knowledge base is the ground; the masters are a compiled layer on top. When the human asks a question, retrieve first, then answer only from what you retrieved.

## Two modes: QUESTION vs TASK

The human’s message is one of two kinds, and each has its own path:

- **QUESTION mode** — “ما سقف الكلمات في الرسالة؟” / “what’s the reply rate ceiling?” — wants a specific fact. Path: `search` → cite passages → answer.
- **TASK mode** — “اعملي بزنس بلان” / “draft me an outreach campaign” / “ابني البزنس بتاعي” — wants the model to *become the specialist and execute*. Path: `route` → **read the master(s) in full** → execute using only what they say.

The distinction is the whole point of the masters (MASTER_GUIDE.md): a master is a topic expert in one file — reading it once makes the model fluent. Task mode is where that promise is cashed in.

## Steps
1. **Classify the request:** task (build/draft/plan something — use `route` below) or question — pin‑point (one passage), broad (whole topic), comparison (two views), relational (who/why links).
2. **Filter by topic** so you search the right namespace. For a comparison, run the search once per side.
3. **Route:** read the relevant `INDEX.md`, then the master hub, then the specific concepts/atoms — the smallest sufficient set, not everything.
4. **Retrieve — with the engine, not by hand.** Keyword search is the baseline and works everywhere with no dependencies:
   ```bash
   python3 tools/retriever.py index                     # (re)build after any bulk change
   python3 tools/retriever.py search "سؤالك" -k 10      # BM25, Arabic-normalized tokens
   python3 tools/retriever.py search "query" --topic outreach --layer concept
   ```
   The index is SQLite (`.kforge/index.db`, gitignored) and rebuilds in seconds; tokens are normalized for Arabic (hamza/taa-marbuta/alef-maqsura folding, diacritics stripped) so spelling variants still match. If you add semantic/vector search to catch different phrasings, treat it as an add‑on you **measure before trusting** — not a default.
5. **TASK mode — become the expert, then execute:**
   ```bash
   python3 tools/retriever.py route "اعمل حملة أوتريتش جديدة" -m 3
   ```
   `route` ranks the masters whose content matches the task and returns a **reading order** (hub first, then sub-masters, each with its `question:`, level and size). Read every listed master **in full** — not excerpts — then execute the task from that expertise alone, citing sources for claims and flagging gaps as “not in the sources”. If `route` returns nothing, the topic is not built yet: say so and propose building it (sources → atoms → concepts → master) instead of improvising an answer.
6. **Expand for broad questions** to whole concepts/pages and the topic’s master hub.
7. **Show both sides** when a tension (`X_`) exists.
8. **Generate only from retrieved passages**, never from training memory.
9. **Cite every claim** with its source file. A sentence with no backing passage is dropped or marked “unsupported.”
10. **If there is no evidence, say “not in the sources.”** Do not guess. Weak lexical matches (a question sharing common words with a passage) are not evidence — check the retrieved text actually answers the question.

## Evaluation (optional but recommended)
`eval/questions.yml` holds questions whose answers live in known passages. Measure **recall@k** (did the right passage appear in the top k) and **faithfulness** (share of answer sentences actually backed by a passage) with `tools/evalrun.py`:

```bash
python3 tools/evalrun.py -k 10                       # recall@k for every question
python3 tools/evalrun.py --answer answers.md         # + faithfulness per question ("## Q<id>" sections)
```

Measurement is separated from generation: the tool never generates answers, it only scores them. Include a question with `expected: []` to test the “not in the sources” path. Don’t expand the base before a known‑answer test passes.
