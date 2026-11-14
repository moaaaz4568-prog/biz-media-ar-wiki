# Structure — folder layout

```
knowledge-forge/
├── README.md            # for the human
├── AGENT.md             # the one instruction file for the AI
├── config.yml           # per‑project settings (language, topics, gate thresholds)
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
├── sources/             # YOUR files go here, whole and unedited (read‑only witnesses)
│   └── INDEX.md
├── atoms/<topic>/       # T_ verbatim quotes
├── concepts/<topic>/    # C_ knowledge units
├── tensions/            # X_ conflicts kept side by side
├── glossary/            # G_ term entries
├── masters/<topic>/     # M_ topic experts (hub + sub‑masters)
├── synthesis/           # Y_ cross‑master patterns
├── eval/                # known‑answer questions + measurement runs
│   └── questions.yml
├── rejected/            # off‑topic content, MOVED here (never deleted)
└── archive/             # anything “removed”, MOVED here with a reason (never deleted)
```

Every content folder has an `INDEX.md` listing what is inside and each file’s purpose. `tools/` scripts (optional, measurable checks) may be added later by whoever runs the project.
