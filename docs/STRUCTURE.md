# Structure — folder layout

```
knowledge-forge/
├── README.md            # for the human
├── AGENT.md             # the one instruction file for the AI
├── AGENTS.md            # agent-discoverable summary (tools + core commands)
├── config.yml           # per‑project settings (language, topics, gate thresholds, master levels)
├── LICENSE
├── LOG.md               # dated work log; every entry names the command used to measure it
├── DECISIONS.md         # decision + rejected alternative + reason
├── docs/                # the method (read‑only reference)
│   ├── PRINCIPLES.md
│   ├── ONTOLOGY.md
│   ├── GATES.md
│   ├── STRUCTURE.md
│   ├── CONCEPT_GUIDE.md
│   ├── MASTER_GUIDE.md
│   └── RETRIEVAL.md
├── tools/               # the method, executable (Python stdlib only)
│   ├── gates.py         # C1–C8 / M1–M8 as code + D8 self-test
│   ├── retriever.py     # BM25 retrieval engine (SQLite, Arabic-normalized)
│   ├── evalrun.py       # recall@k + faithfulness measurement
│   └── kforge/          # shared library (front-matter, YAML subset, Arabic normalization)
├── sources/             # YOUR files go here, whole and unedited (read‑only witnesses)
│   └── INDEX.md
├── atoms/<topic>/       # T_ verbatim quotes
├── concepts/<topic>/    # C_ knowledge units
├── tensions/            # X_ conflicts kept side by side
├── glossary/            # G_ term entries
├── masters/<topic>/     # M_ topic experts (hub + sub‑masters, levels L0→L3)
├── synthesis/           # Y_ cross‑master patterns
├── eval/                # known‑answer questions + measurement runs
│   └── questions.yml
├── examples/ar-outreach/ # a complete Arabic example KB that passes all gates
├── rejected/            # off‑topic content, MOVED here (never deleted)
└── archive/             # anything “removed”, MOVED here with a reason (never deleted)
```

Every content folder has an `INDEX.md` listing what is inside and each file’s purpose. The `.kforge/` directory (search index) is generated — gitignore it and rebuild with `tools/retriever.py index`.
