---
type: concept
topic: shop-ops
confidence: high
class: causal
sources: [sources/S_ops_handbook.md]
---

# C_staffing_floor — The Three-Person Floor

## Definition

The staffing floor is the minimum of three people on a trading shift:
one on till, one on bar, one floating. It is a hard line drawn from a
measured failure — the queue reaching the door — not a staffing
preference.

## Mechanism

Three roles absorb each other's spikes. The floater covers the till
during a bar backlog and the bar during a till queue, so neither queue
grows unbounded. Below three, the floater merges into bar permanently:
the till queue then grows at the full arrival rate with no relief, and
in the shop's own measurement it hit the door in eighteen minutes. The
floor exists because the failure mode is fast, visible to every
customer, and starts before the team feels understaffed.

## Limits — when it breaks

- During a scheduled deep-clean close, two people are acceptable because
  the till is closed and the door is locked.
- The floor says nothing about rushes above normal volume — three people
  hold the line at typical flow, not at a festival crowd.
- It assumes the on-call list was called BEFORE hitting three, not
  after; a late call breaks the floor even with three on paper.

## Conditions

- Is the shop in trading hours? (The rule is for open doors only.)
- Was the call made before the count dropped to three?

## Evidence

- "A shift needs a minimum of three people: one on till, one on bar, one floating" — sources/S_ops_handbook.md
- "Below three, the floater merges into bar and the till queue grows past the door within twenty minutes" — sources/S_ops_handbook.md
- "we measured this in October 2025 during the bridge closure week and the queue hit the door in eighteen minutes flat" — sources/S_ops_handbook.md

## Provenance

- sources/S_ops_handbook.md

## Tensions

- (none)
