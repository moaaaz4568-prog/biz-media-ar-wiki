# Work log

> Every entry names the command used to measure it. A number with no command is void.

| Date | What happened | Measured by | Result |
|---|---|---|---|
| 2026-11-14 | Template restructured into a monorepo: `knowledge-forge/` became the root; personal context files (context.md, n.md, prompt.md) removed from the public template | `find . -name "*.md" \| wc -l` | 0 personal files remain in the template |
| 2026-11-14 | Gates made executable: tools/gates.py (C1–C8, M1–M8, byte-exact quote checks, wiki-link resolution) | `python3 tools/gates.py self-test` | 16/16 gates can fail (D8) |
| 2026-11-14 | Graduated master levels L0→L3 added to config.yml and enforced per-file via `master_level` | `python3 tools/gates.py master masters/outreach/M_outreach_hub.md` | L0 master ACCEPTED (6 sections / 2,013 words) |
| 2026-11-14 | Retrieval engine added: BM25 over Arabic-normalized tokens, SQLite index in .kforge/ | `python3 tools/retriever.py index` | 7 files → 47 chunks, 3,214 words |
| 2026-11-14 | Known-answer evaluation measured on the example KB (8 real + 1 known-absent question) | `python3 tools/evalrun.py -k 10` | recall@10 = 8/9 = 0.889 (target 0.8; the miss is q9, intentionally unanswerable) |
| 2026-11-14 | Faithfulness measured on a sample answer file | `python3 tools/evalrun.py -k 10 --answer eval/sample_answers.md` | q2: 2/2 sentences backed (100%) |
| 2026-11-14 | Example KB built under examples/ar-outreach/ (1 source, 2 atom files, 2 concepts, 1 tension, 1 L0 master) | `python3 tools/gates.py check` (from examples/ar-outreach) | 3 entities, 0 rejected |
