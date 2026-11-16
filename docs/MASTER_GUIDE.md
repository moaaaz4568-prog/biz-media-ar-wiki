# Master guide — how to build an `M_`

A master is a **topic expert in one file**: reading it once makes the model fluent in that topic. It answers **one question** (set in front‑matter). It is built from the topic’s concepts, **not** from a template.

## Choose the shape: hub + sub‑masters (recommended)
Three options exist, from the original idea:
1. One giant master per topic — rejected: too big to fit in one context as the topic grows.
2. A master per sub‑folder only — rejected: loses the big picture.
3. **Hub pattern (recommended):** a *main master* that explains the topic broadly and, in each section, links to a focused *sub‑master* by its path (e.g. a “how‑to” sub‑master). Big picture first, depth on demand. A huge topic is split into sub‑masters.

## Suggested sections
The exact count is set in `config.yml` (`master.sections`). A solid default set:
1. TL;DR (a working promise, not a summary) — written **last**.
2. Philosophy (why the topic works at all) — causal, no recommendations.
3. Definitions (term · meaning · difference from its look‑alike neighbor).
4. **Systems & how‑to** — the densest section (≥ 40% of the master).
5. Numbers (each tagged with how it was measured, or dropped).
6. Common mistakes (symptom + fix + the condition where the fix breaks).
7. Variables (when the rules flip, not when they apply).
8. Evidence (attributed verbatim quotes).
9. Tensions + the discriminator that separates the sides.
10. Ready‑to‑use templates (each with a “when it breaks” line).
11. Checklist.
12. Scenarios (a real decision under pressure: constraints · two options · cost · recommendation).
13. Tools (+ when each goes stale).
14. KPIs reasoned backward from the end goal.
15. **Independent analysis** — your own patterns, the knowledge gap, a framework (substantial).
16. Q&A (operational questions, each answer pointing to a section).
17. Links to other masters (`[[M_...]]`).
18. Concept index — links to **every** concept of the topic as real `[[C_...]]`.

## Build order
Write **section 4 first** (densest), then the independent‑analysis section, then the rest; write the TL;DR **last** (it is a promise, not an intro). Then run the master gates, then human‑review the how‑to and analysis sections, then set `status: complete` and add a dated row to `LOG.md`.

## Survival rules (from how these fail)
- If content exceeds a ceiling, **summarize, do not truncate** mid‑sentence.
- Never write a link before the target file exists — verify the exact name first.
- When a number conflicts with another source, show **both** with their sources; do not pick silently.
- Apply the dead‑recipe test (`docs/PRINCIPLES.md`).
- The goal: the reader comes out **able to act, not just having read** — running the knowledge without going back to the source.
