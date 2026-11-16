# Ontology — the layers and strict naming

The knowledge base is a chain of layers that must never blur into each other. Each entity type has **one prefix, one folder, one `type:` value**. All three must agree — this triple‑match is what prevents layer‑mixing (the single most common way these systems rot).

## The chain
`S_ source → T_ atom → C_ concept → X_ tension → M_ master → Y_ synthesis`

| Entity | Prefix | Folder | `type:` | What it is |
|---|---|---|---|---|
| Source | `S_` | `sources/` | `source` | The original document. Read‑only. The only witness. |
| Atom | `T_` | `atoms/` | `atom` | A single verbatim quote from a source, with its location, **no interpretation**. |
| Concept | `C_` | `concepts/<topic>/` | `concept` | One unit of knowledge built from atoms: definition + mechanism + limits + evidence. |
| Tension | `X_` | `tensions/` | `tension` | A documented conflict between two views, plus the condition that separates them. |
| Glossary | `G_` | `glossary/` | `glossary` | A term entry: name, synonyms (`aka:`), origin, one live example. |
| Master | `M_` | `masters/<topic>/` | `master` | A topic expert file that answers one question. Built from its topic’s concepts, not from a template. |
| Synthesis | `Y_` | `synthesis/` | `synthesis` | A pattern drawn from ≥3 masters. Read after masters, not instead of them. |

## Promotion rules (the source always stays)
- `T_ → C_`: when an idea appears in ≥2 atoms and you can explain its mechanism. The atom stays.
- `C_ → X_`: when two concepts conflict.
- `X_ → M_`: when the conflict matters for a topic’s answer.
- `M_ → Y_`: when ≥3 masters agree on a pattern.

## Always forbidden
- **Merging** (deleting the original).
- **Copying** (duplicating under another name).
- **Auto‑promotion** without passing a gate.

## The atom vs concept line
An atom is **a sentence that exists in a file**. A concept is **something you wouldn’t want as a bare file** — an interpretation built from atoms. The difference is not length; it is *restraint*: an atom carries no analysis.
