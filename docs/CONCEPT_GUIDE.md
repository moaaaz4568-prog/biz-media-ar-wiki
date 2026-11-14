# Concept guide — how to write a `C_`

A concept is an interpretation built from atoms. The difference from an atom is **restraint**, not length: an atom carries no analysis; a concept does.

## Sections (fixed order)
1. **Definition** (15–60 words).
2. **Mechanism** — *why* it works (80–200 words, causal, does not start with an imperative).
3. **Limits / when it breaks** — ≥3 bullets, each naming the variable that breaks it (“when X changes”, not “when conditions change”).
4. **Conditions** — ≥2 bullets each answerable yes/no.
5. **Evidence** — ≥3 verbatim quotes ≤60 words each, format `- “quote” — source_id`, plus two lines: *confidence* and *source bias*.
6. **Provenance** — rows of `source_id`.
7. **Tensions** — links to any `X_` where this concept conflicts with another.

## Front‑matter (YAML)
`type: concept` · `topic:` · `confidence: high|med|low` · `class: causal|formula` · `sources:` (≥1, never empty).

## Evidence must be byte‑exact
A re‑typed/paraphrased quote is fake evidence. Copy the quote exactly as it appears in the source. If you cannot find it verbatim in a source file, you cannot use it.

## Redirect instead of merge
To retire a concept, do not merge (that deletes the original). Create `type: redirect` with `redirect_to:` and a mandatory `why:` line. The target must be a real, kept entity.
