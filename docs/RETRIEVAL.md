# Retrieval — how the AI answers questions

The knowledge base is the ground; the masters are a compiled layer on top. When the human asks a question, retrieve first, then answer only from what you retrieved.

## Steps
1. **Classify the question:** pin‑point (one passage), broad (whole topic), comparison (two views), relational (who/why links).
2. **Filter by topic** so you search the right namespace. For a comparison, run the search once per side.
3. **Route:** read the relevant `INDEX.md`, then the master hub, then the specific concepts/atoms — the smallest sufficient set, not everything.
4. **Retrieve — with the engine, not by hand.** Keyword search is the baseline and works everywhere with no dependencies:
   ```bash
   python3 tools/retriever.py index                     # (re)build after any bulk change
   python3 tools/retriever.py search "سؤالك" -k 10      # BM25, Arabic-normalized tokens
   python3 tools/retriever.py search "query" --topic outreach --layer concept
   ```
   The index is SQLite (`.kforge/index.db`, gitignored) and rebuilds in seconds; tokens are normalized for Arabic (hamza/taa-marbuta/alef-maqsura folding, diacritics stripped) so spelling variants still match. If you add semantic/vector search to catch different phrasings, treat it as an add‑on you **measure before trusting** — not a default.
5. **Expand for broad questions** to whole concepts/pages and the topic’s master hub.
6. **Show both sides** when a tension (`X_`) exists.
7. **Generate only from retrieved passages**, never from training memory.
8. **Cite every claim** with its source file. A sentence with no backing passage is dropped or marked “unsupported.”
9. **If there is no evidence, say “not in the sources.”** Do not guess. Weak lexical matches (a question sharing common words with a passage) are not evidence — check the retrieved text actually answers the question.

## Evaluation (optional but recommended)
`eval/questions.yml` holds questions whose answers live in known passages. Measure **recall@k** (did the right passage appear in the top k) and **faithfulness** (share of answer sentences actually backed by a passage) with `tools/evalrun.py`:

```bash
python3 tools/evalrun.py -k 10                       # recall@k for every question
python3 tools/evalrun.py --answer answers.md         # + faithfulness per question ("## Q<id>" sections)
```

Measurement is separated from generation: the tool never generates answers, it only scores them. Include a question with `expected: []` to test the “not in the sources” path. Don’t expand the base before a known‑answer test passes.
