# Namespaces & Isolation

> A namespace is one corpus with one voice. Isolation is structural, never a prompt hint.

## What a namespace is

A namespace is a knowledge base directory: `namespaces/<name>/` (or
`examples/<name>/`), holding its own `config.yml` and its own layer
folders (`sources/`, `glossary/`, `atoms/`, `concepts/`, `tensions/`,
`masters/`, `synthesis/`, `eval/`, `rejected/`). One namespace = one
topic, one person, one team handbook — whatever the user defines.

- The **folder name is the namespace id** — the thing `--namespace`
  addresses. A copied `config.yml` saying a different name does not
  rename a KB (the folder wins).
- Namespaces are **siblings, never nested** inside each other.
- Each namespace has its **own index** (`.kforge/index.db` + optional
  `.kforge/vec.db`). Retrieval, answering, and synthesis never mix
  namespaces unless the user explicitly asks for cross-namespace
  synthesis.

## Why structural, not a prompt hint

A prompt hint ("only use namespace A") fails silently under pressure:
the model gets a tempting passage from B and cites it in A's voice. A
separate SQLite file cannot leak by accident — searching namespace A
literally never opens namespace B's index. This is the single most
important structural decision in v2: the most dangerous failure is a
confident answer in one voice cited to another's text, and only
structural separation prevents it.

## The leak test (canaries)

Every namespace plants a canary passage (`sources/CANARY-<ns>.md`)
carrying a unique marker `CANARY-<ns>`. The leak test queries each
namespace with every OTHER namespace's canary text and fails if any
returned passage contains the other's marker:

```bash
python3 tools/forge.py verify    # runs the leak test among its checks
```

Shared boilerplate between canaries is expected to match lexically —
that is the adversarial part. Only the marker's presence in a returned
passage proves cross-namespace content. `forge ask` and the MCP
`answer` tool filter `sources/CANARY-*` passages out of every answer
(D20).

## Cross-namespace synthesis (`Y_`)

Cross-namespace synthesis is a separate, DECLARED operation: a `Y_`
file reads ≥3 masters from different namespaces, cites every claim with
its namespace, and labels itself cross-namespace. It is never the
default path, and it is the ONLY entity allowed to link across
namespace boundaries (gate N1 enforces this on every file).

## Per-namespace config

`config.yml` per namespace: language (picks the normalizer plugin —
see `kforge/langs.py`), topics, gate thresholds, master levels, system
voice, and the pinned embedding model + dimension. Changing the
embedding model or dimension requires a full vector rebuild —
`tools/embed.py` enforces this by dropping the store, not by documenting
it.

## Commands

```bash
python3 tools/forge.py init <name> --language en   # scaffold (folders, config, canary, eval skeleton)
python3 tools/forge.py build --namespace <name>    # pipeline + gates + eval, stops on failure
python3 tools/forge.py status                      # what is built, per namespace
python3 tools/retriever.py search "q" --namespace <name>
python3 tools/forge.py ask "q" --namespace <name>
```
