# Work log

> Every entry names the command used to measure it. A number with no command is void.

| Date | What happened | Measured by | Result |
|---|---|---|---|
| 2026-11-14 | Example KB seeded: 1 source, 2 atom files, 2 concepts, 1 tension, 1 L0 master | `python3 ../../tools/gates.py concept concepts/outreach/C_first_line_personalization.md` | both concepts ACCEPTED, quotes byte-exact |
| 2026-11-14 | Master M_outreach_hub built at level L0 (6 sections) | `python3 ../../tools/gates.py master masters/outreach/M_outreach_hub.md` | ACCEPTED at L0 thresholds |
| 2026-11-14 | Retrieval index built over the example KB | `python3 ../../tools/retriever.py index` | indexed 7 files |
| 2026-11-14 | recall@10 measured on 8 known-answer questions | `python3 ../../tools/evalrun.py -k 10` | 8/8 = 1.000 (target 0.8) |
