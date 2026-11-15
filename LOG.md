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
| 2026-11-14 | TASK mode added: retriever route — ranks masters per task, hub-first reading order with question/level/words | `python3 tools/retriever.py route "ابني حملة أوتريتش" -m 2` | M_outreach_hub ranked #1 (score 7.4) |
| 2026-11-14 | Arabic definite-article folding in tokenizer ('البريد' == 'بريد'), symmetric on index and query | `python3 tools/tests/run_all.py` | 16/16 passed; 'ما سقف عدد الكلمات' now ranks C_length_100 first |
| 2026-11-14 | RETRIEVAL.md split into QUESTION vs TASK modes; AGENT.md/AGENTS.md/README updated with route | `python3 tools/gates.py self-test` | 16/16; example KB recall@10 unchanged at 0.889 |
| 2026-11-15 | v2 core: language normalizer registry (kforge/langs.py), namespace paths, hybrid retrieval (BM25+dense RRF fusion), embed.py (ONNX e5, sqlite-vec), gates T1-T4/X1-X4/G1-G2/N1/M9/M10 | `python3 tools/gates.py self-test` | 26/26 gates can fail (D8) |
| 2026-11-15 | Baseline re-verified on a clean GitHub clone (moaaaz4568-prog/knowledge-forge) | `python3 tools/gates.py check` + `tools/tests/run_all.py` + `tools/evalrun.py -k 10` | gates 3 entities/0 rejected; tests 16/16; recall@10 = 0.889 (matches the brief exactly) |
| 2026-11-15 | Second example en-handbook/ built (EN, shop-ops): glossary-first, 3 atom files, 2 concepts, 1 tension, L0 master 2,102 words, 13 eval questions in 4 tiers | `python3 tools/gates.py check --namespace en-handbook` | 9 entities, 0 rejected |
| 2026-11-15 | Graduated evaluation (tiers) measured on ar-outreach: keyword vs hybrid, same 12 answerable questions | `python3 tools/evalrun.py --compare-engines` (from examples/ar-outreach) | paraphrase tier: keyword 3/4 = 0.750 -> hybrid 4/4 = 1.000 (q12 clickbait question missed by BM25, caught by dense); exact/comparison 1.000 both engines |
| 2026-11-15 | Leak test (canary markers CANARY-<ns>): query each namespace with the other's canary text | `python3 tools/forge.py verify` | 2 namespaces x 2 canaries — zero cross-namespace passages |
| 2026-11-15 | forge verify (one-command rule, idea 11): gates self-test + check + unit tests + per-ns eval + leak test | `python3 tools/forge.py verify` | VERIFY: PASS (8 checks, ~10s) |
| 2026-11-15 | Constrained answering measured (forge ask, glm-4-plus via z-ai bridge, hybrid engine) | `python3 tools/forge.py ask "كم متابعة تكفي وبعد كم يوم؟" --namespace ar-outreach` | faithfulness 2/2 = 1.00; 2.2s; receipt 20261115-192130 |
| 2026-11-15 | TASK mode measured (forge do): master read in full, checklist executed from master content | `python3 tools/forge.py do "write the opening checklist for tomorrow's 6am shift" --namespace en-handbook` | all 5 checklist items sourced from M_shop_ops_hub; 3.1s |
| 2026-11-15 | "not in the sources" contract tested in both languages (unanswerable tier questions) | `python3 tools/forge.py ask` (q9 ar + q9 en) | both return exactly "not in the sources" |
| 2026-11-15 | MCP server end-to-end with a real JSON-RPC client over stdio | `python3 tools/tests/test_mcp_client.py` | 11/11 checks PASS (search, containment, cited answer, receipt, unanswerable, route, error paths) |
| 2026-11-15 | Embedding model comparison on the same eval sets: e5-small (118MB, 384d) vs e5-large (562MB, 1024d) | `python3 tools/embed.py index --model <m> --namespace <ns>` + `tools/evalrun.py --engine hybrid` | recall@10 both 1.000 on both examples; cost: e5-small 9.2s/11.9s vs e5-large 38.2s/48.5s (~4x) -> e5-small is the default (decision D14) |
| 2026-11-15 | Rerank (gte-multilingual-reranker-base int8) on/off over fused candidates | `python3 tools/evalrun.py --engine hybrid --rerank` | recall@10 unchanged at 1.000 on both examples (sets saturated; rerank stays optional, off by default — decision D15) |
| 2026-11-15 | Incremental indexing verified: glossary file added, only that file re-chunked | `python3 tools/retriever.py index` | "9 files -> 53 chunks (1 re-chunked, 8 unchanged)" |
| 2026-11-15 | eval/ excluded from the index after the sample_answers.md hallucination demo poisoned the unanswerable path (retrieved as top-1 and the LLM followed it) | retest `tools/forge.py ask` on the ar unanswerable question | before: hallucinated "اللون الأزرق يرفع الثقة 40%" with fake [sources/S_x.md]; after: exactly "not in the sources" |
