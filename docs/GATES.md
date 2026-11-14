# Gates — measurable quality checks

Every gate is a check you can run and that returns pass/fail. **A gate that can never fail is broken** — before trusting any gate, test it once with a case you know should fail, and confirm it fails.

Three severities: **blocker** (entity is rejected until fixed) · **high** (accepted with a visible warning) · **low** (logged only).

**The gates are executable** — `tools/gates.py` implements this file. Run it from the knowledge‑base root:

```bash
python3 tools/gates.py check                      # scan every concept/master
python3 tools/gates.py concept concepts/t/C_x.md  # one entity
python3 tools/gates.py master   masters/t/M_x.md  # one entity
python3 tools/gates.py self-test                  # D8: prove each gate can fail
```

`self-test` feeds every gate a known‑bad input and fails loudly if any gate passes it — run it whenever the tool or the rules change. The tool also verifies C5 quotes **byte‑exact against `sources/`** and resolves wiki‑links (`[[path|alias]]`) to real files.

Master thresholds are **graduated** (see `config.yml` → `master.levels`): a master declares its level in front‑matter (`master_level: L0..L3`); L0 accepts 6 sections / 2,000 words, L3 requires the full 18 / 10,000. Promotion between levels is a human decision recorded in `LOG.md`.

## Concept gates (`C_`)
| ID | Check | Threshold | Severity |
|---|---|---|---|
| C1 | Triple match: `type:` × filename prefix × folder all agree | 3/3 | blocker |
| C2 | Has a definition section | 1 | blocker |
| C3 | Has a mechanism explaining *why* it works | ≥40 words | high |
| C4 | Has “limits / when it breaks”, naming the variable that breaks it | ≥3 items | blocker |
| C5 | Has ≥3 verbatim quotes, each with a source id (tool: byte‑exact in `sources/`) | ≥3 | high |
| C6 | Depth within range | 250–600 words | low |
| C7 | No placeholders (TODO/TBD/XXX) | 0 | blocker |
| C8 | ≥1 outgoing link `[[C_...]]` or `[[M_...]]` | ≥1 | low |

## Master gates (`M_`)
| ID | Check | Threshold | Severity |
|---|---|---|---|
| M1 | Exactly the required number of sections, none duplicated | = N (per level) | blocker |
| M2 | Total length | ≥ min for level | blocker |
| M3 | The “Systems & how‑to” section is the densest part | ≥ 40% of words | high |
| M4 | The “independent analysis” section is substantial | ≥ min for level | high |
| M5 | The concept‑index section links to every concept of the topic, all links real | 0 broken | blocker |
| M6 | Full front‑matter + triple match | valid | blocker |
| M7 | Every how‑to recipe has a “when it breaks” line | 0 missing | blocker |
| M8 | `status: complete` + a dated row in `LOG.md` | present | blocker |

## Three things that drop a master instantly
1. A recipe with no “when it breaks” line.
2. A broken link in the concept‑index section (points to a file that doesn’t exist).
3. A duplicated section.

## What the machine cannot see
A fake “when it breaks” line passes the automated check. So **human review of the how‑to and analysis sections is mandatory**, not optional. Separate structure‑checking (files exist, shape is right) from content‑checking (information is correct) — passing the first never implies the second.
