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
| D13 | Namespaces are structural (one index per KB, folder name is the id) | Prompt-level hints ("only use namespace A") | A prompt hint fails silently under pressure; separate SQLite files cannot leak by accident (§7) |
| D14 | e5-small (118MB int8 ONNX) is the default dense model | e5-large / bge-m3 | Measured equal recall@10 (1.000) on both example sets; e5-large costs ~4x the embed time (38–49s vs 9–12s per namespace) with no gain at this corpus size; bge-m3 is 570MB for the same 1024d class |
| D15 | Rerank is optional and OFF by default | Always-on cross-encoder | Measured: recall@10 unchanged (1.000) with rerank on both examples (saturated sets); a 341MB model in the hot path buys nothing here — stays a flag, re-measured when a tier drops below target |
| D16 | The z-ai CLI is the LLM bridge (optional rung) | Hardcoding an API/key in tools | The core loop never calls it; when absent, answers degrade to retrieval-only and the receipt SAYS so (idea 14) |
| D17 | eval/ folders are excluded from indexing | Index everything | Measured failure: the faithfulness demo file (containing a deliberate hallucinated answer) was retrieved as top-1 and the LLM followed it — eval scaffolding must never be answerable content |
| D18 | Quote "byte-exact" = same words in order, line-wrap insensitive | Raw byte comparison | Sources wrap at ~72 cols; a re-wrapped quote is still a faithful quote. Folded-whitespace comparison on both sides keeps the guarantee (nothing added/dropped) while quotable |
| D19 | MCP server is read-only (search/answer/route) | Write tools over MCP | Any model can read the base; no model gets a write path that bypasses the gate-checked CLI pipeline (§8.2) |
| D20 | Canary passages carry CANARY-<ns> markers and are excluded from answers | Plain canary text | Marker-in-returned-passage is the only reliable leak signal (shared boilerplate would false-positive); ask/answer filter CANARY- paths from the passage list |
