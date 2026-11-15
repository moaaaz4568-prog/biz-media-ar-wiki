---
type: master
topic: shop-ops
question: "How do I run a shift at Riverside Coffee Co. without burning quality or cash?"
master_level: L0
status: complete
hub: true
built_from_hash: 1c83f9296728d31ca0d6ae7f5028297d6de56dd1
---

# M_shop_ops_hub — Shift Running (L0)

## TL;DR

This master packs the Riverside Coffee Co. operations handbook into
rules a shift lead can run a day on. The working promise: follow these
rules and the morning rush holds quality, the till balances, and nobody
gets hurt silently. The four anchors: warm the machines forty minutes
before the first shot, keep the pull inside 25–30 seconds by adjusting
grind not dose, hold three people on every trading shift, and log
everything — waste before it is thrown, injuries within the shift, cash
twice with initials. Every rule here carries its literal evidence from
the handbook, and each names the condition where it breaks. This is the
L0 first build: six sections, growing with the base.

## Systems & how-to

### Step 1: Open on the clock, not before it

Arrive at 6:00 and pull yesterday's cash report first. Turn the espresso
machines on the moment you walk in — they need forty minutes before they
pull a shot worth serving — then count cash while they heat. Unlock the
front door at 6:30, never earlier: the alarm grace period ends at 6:25
and an early door costs a false dispatch fee. Milk arrives at 5:50 in
the back alley; check every crate's temperature and refuse anything
above 4 degrees Celsius, no exceptions — the August 2025 broken-fridge
day, when the shop served nothing but black coffee until noon, is why
this rule exists.

When it breaks: if you arrive late, do NOT unlock early to "make up
time" — the fee is certain and the minutes are not; instead delay the
door and note it in the log.

### Step 2: Dial the espresso by the clock

The shot clock is the heart of quality control: a double espresso pulls A double espresso should
pull between 25 and 30 seconds;. Shorter tastes sour; longer tastes bitter
and muddy. When the time drifts, adjust the grind, not the dose —
changing the dose to fix timing hides the real problem and teaches new
baristas the wrong habit. Note the weather at dial-in: rainy days make
the same setting pull slower, dry days faster, so expect to re-dial
after any weather front. The dial is a morning instrument reading, not
a set-and-forget number.

When it breaks: when shots creep past 32 seconds for a whole morning
even after adjustment, the grinder blades are worn — order replacements
the same day, because the courier does not run Sundays.

### Step 3: Staff the floor at three, call before you fall

A trading shift needs a minimum of three people: one on till, one on
bar, one floating. Below three, the floater merges into bar and the
till queue grows past the door within twenty minutes — measured in
October 2025 during the bridge closure week, when it hit the door in
eighteen minutes flat. Call the on-call list BEFORE you hit three, not
after. Breaks are 30 minutes paid, taken in order of who started first;
no one works more than four hours without a break. Rota reality check:
the software only flags missed breaks if the rota was actually built in
the software, not on a sticky note.

When it breaks: during a scheduled deep-clean close, two people are
acceptable — the till is closed and the door is locked; the floor
applies to trading hours only.

### Step 4: Train bar first, till second

New baristas train two weeks on bar before they touch the till, because
till mistakes cost money quietly while bar mistakes are loud and
fixable. The training checklist lives in the binder by the office door;
the trainee signs each stage and the shift lead countersigns. A skipped
countersign is a skipped stage, whatever the trainee says they know.

When it breaks: if the binder is missing, training pauses — do not run
unsigned stages from memory, because the checklist is the only shared
definition of "trained".

### Step 5: Close the cash twice, log waste first

The till is counted at 21:00 by the closing lead and again at 6:05 by
the opening lead; both counts go in the cash book with initials. A
variance over 5 pounds triggers a same-week count-together session with
the manager — not punishment, but because variance that survives a week
becomes untraceable. Tips split by hours worked from the POS hours
report, rounded up to the nearest pound per person; cash tips stay in
the jar, card tips ride the Friday payroll. Every pour-out, expired
pastry, and dropped cup is logged with a reason code BEFORE it is
thrown away, because the monthly P&L treats unlogged waste as
theft-pattern noise and hides real problems like Tuesday over-ordering.

When it breaks: if the POS hours export fails, split from the rota's
clock-in records and note the substitution — an unlogged method choice
is how tip disputes start.

### Step 6: Injuries and incidents — write it down within the shift

Any injury, however small, goes in the incident book within the shift it
happened. The book is a legal document: date, time, person, what
happened, what was done, signature. First aid supplies live in the kit
by the grinder, and plasters are blue-detectable only — a normal plaster
in a drink is a hygiene incident, a blue one is a near-miss, and the
difference is the whole reason the rule exists.

When it breaks: if the injury needs outside care, the handbook is
explicit — call 999 first, the contact tree second. The tree is for
coverage and decisions, not for permission to call for help.

### Step 7: Broken equipment is tagged out, never worked around

A broken steam wand is not "the one we do hot water from" — it is off,
tagged, and the tag carries the date and the fault. Working around a
fault teaches the whole team to ignore tags, and the day someone ignores
a tag on the oven, that habit is the injury. Tag discipline is a safety
rule wearing an operations costume: it looks bureaucratic until it is
the only thing between a rushed morning and a burn.

When it breaks: if no tags are in stock, the equipment goes OFF and a
written note on the office board stands in — the point is a visible,
dated record, not the tag itself.

### Full measurement doctrine

Every number in this master comes from the handbook's own measurements
(the eighteen-minute queue, the 4-degree milk rule, the 40-minute
warm-up). When a new shift lead wants to change a number, they measure
first: same conditions, one variable, results in the log. A number
without a measurement behind it is an opinion wearing a number's
clothes.

### Working terms in this master

Shot clock, staffing floor, floater, dial-in, tag-out — see the
glossary entries [[G_shot_clock]] and [[G_min_staffing]].

## Tensions

- [[X_dial_vs_blades]] — is a slow shot a dial problem or a blade
  problem? The handbook holds both views with a clean discriminator:
  humidity drift corrects with a same-morning adjustment; blade wear
  persists "even after adjustment" for a whole morning. Read the
  tension before ordering blades on the first slow morning.

## Independent analysis

The handbook's rules share one property: each exists because of a
recorded failure, and each names the failure's cost. The 6:30 door rule
costs a dispatch fee when broken; the milk rule cost a black-coffee
noon; the staffing floor cost an eighteen-minute queue; the blade rule
costs a Sunday with no grinder. This is failure-priced rule-making, and
it explains what a generic manual gets wrong: a rule that names its
cost survives a busy morning, a rule that only states the behavior gets
traded away under pressure.

The gap the handbook does not cover: single shots have no time band
(the source only defines the double), rush staffing above normal volume
is undefined beyond the three-person floor, and the waste-log reason
codes are referenced but never listed. A shift lead should treat those
three as open questions for the ops team, not as silent permissions.

A framework for reading any rule in this master: (1) what failure
created it, (2) what it costs to follow, (3) what it costs to break,
(4) the condition where it stops applying. If any of the four is
missing, the rule is a habit, not a rule — file a change request.

There is also a pattern the handbook repeats quietly: every logging rule
(ex cash twice, waste before discarding, incidents within the shift)
shares the same rationale — an unlogged event becomes untraceable, and
untraceable events compound. Variance that survives a week cannot be
investigated; unlogged waste reads as theft-pattern noise in the P&L; an
unwritten injury cannot be defended in a claim. The handbook is not in
love with paperwork; it is in love with the ability to answer questions
later. That is why the rules demand timing (within the shift, before it
is thrown away) rather than merely completeness — a log filled at the
end of the week is a memory, not a record.

The second quiet pattern: every rule names its own exception inside
itself. The door has 6:30 but never before 6:25's grace end; the
staffing floor has the deep-clean exception; the blade rule has the
Sunday courier caveat. This self-exception style is what makes the
handbook safe to follow under pressure — the operator never has to
improvise the boundary, because the boundary ships with the rule. A
shift lead should distrust any future rule that arrives without its own
break condition attached; that omission is how rulebooks drift from
reality.

## Templates

### Template: morning open checklist

1. 6:00 arrive, pull yesterday's cash report.
2. Machines on immediately (40-minute warm-up).
3. 5:50 milk crates — temperature check, refuse above 4°C.
4. Dial espresso to the 25–30 second band; note the weather.
5. 6:30 unlock the front door (not before 6:25 alarm grace end).

When it breaks: if milk was refused, the black-coffee fallback is the
recorded worst case — decide the menu cut before the door opens, not
during the rush.

### Template: understaffing call

1. Count heads the moment anyone leaves.
2. At three on paper: call the on-call list NOW.
3. Below three: floater merges to bar, expect the door queue in ~20
   minutes; send a runner to manage the door.

When it breaks: if the on-call list yields nobody, the handbook offers
no authorized two-person trading mode — that is a close-the-floor
decision for the manager, not a shift-lead improvisation.

### Operational Q&A

**Can I open the door at 6:20 on a sunny day?** No — the alarm grace
period ends at 6:25; the fee is per false dispatch and it is certain.

**Do I re-dial after rain?** Yes — the same setting pulls slower on
rainy days; dial-in notes the weather for exactly this reason.

### Operational Q&A

**How many counts does the cash book need per day?** Two: the closing
lead counts at 21:00 and the opening lead counts at 6:05 the next
morning, both with initials. A variance over 5 pounds triggers a
same-week count-together session with the manager.

**Where do tips go?** Cash tips stay in the jar; card tips arrive in the
Friday payroll run. The split is by hours worked from the POS export,
rounded up to the nearest pound per person.

**A crate of milk feels cold but reads 5 degrees — can I use it?** No.
The rule is anything above 4 degrees Celsius goes back on the truck, no
exceptions. The August 2025 black-coffee noon is the recorded cost of
bending this one.

**Can I train a new hire on the till in week one if they are quick?**
No — two weeks on bar first, because till mistakes cost money quietly
while bar mistakes are loud and fixable. The checklist in the binder is
the only shared definition of trained; a skipped countersign is a
skipped stage.

**The rota says three but one called in sick and on-call did not
answer — what now?** The handbook offers no authorized two-person
trading mode. Below three, expect the door queue within twenty minutes;
that is a close-the-floor decision for the manager, not a shift-lead
improvisation.

### Pre-close checklist

- Waste logged with reason codes BEFORE discarding.
- Till counted, cash book initialed (21:00 count).
- Tips divided by POS hours, rounded up per person.
- Broken equipment tagged with date and fault — never worked around.

## Concept index

- [[concepts/shop-ops/C_shot_band.md|C_shot_band]] — the 25–30 second pull window and its mechanics.
- [[concepts/shop-ops/C_staffing_floor.md|C_staffing_floor]] — the three-person trading floor and its measured failure.
