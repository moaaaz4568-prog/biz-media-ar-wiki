# Decisions — decision + rejected alternative + reason

| # | Decision | Rejected alternative | Reason |
|---|---|---|---|
| D1 | Generic, reusable repo (any topic, any language) | Hard‑coding one project’s topics/numbers | So anyone can clone it and point it at their own files |
| D2 | Strict triple‑match naming (prefix×folder×type) | Free‑form names | Layer‑mixing is the most common way these bases rot |
| D3 | Concepts before masters | Build masters first | Masters built before concepts are empty shells |
| D4 | Hub master + sub‑masters | One giant master | A giant master won’t fit one context as a topic grows |
| D5 | Show both sides (tensions) | Pick one silently | Silent picking makes a confident, wrong base |
| D6 | Move, never delete (archive/) | Delete | Bulk deletes are irreversible |
| D7 | Keyword search default, semantic optional | Semantic by default | Semantic must be measured before trusting; keyword has no dependencies |
| D8 | Every gate must be tested with a known‑bad case | Trust gates as written | A gate that always passes turns an error into “verified” |
| D9 | Gates are code (`tools/gates.py`), not prose only | Keep gates as documentation | Prose gates depend on the assistant noticing violations; the 3 dead generations rotted exactly there |
| D10 | Graduated master levels L0→L3 | One fixed 18‑section/10k bar | A first master rejected on day one kills the base’s momentum; climbing levels keep quality rising |
| D11 | Retrieval is a BM25 engine (`tools/retriever.py`), keyword‑first | Assume the assistant reads INDEX.md and greps | “Read the indexes” fails at scale and was never measured; BM25 over Arabic-normalized tokens is measurable and dependency-free |
| D12 | Evaluation runs as code (`tools/evalrun.py`), separate from generation | Assert quality informally | recall@k/faithfulness asserted but never measured is a number with no command — void by the LOG rule |
