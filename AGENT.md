# AGENT.md — the one file your AI assistant follows

> **To the human:** put your documents in `sources/`, then tell your assistant: *“Read AGENT.md and follow it.”*
>
> **To the AI assistant:** this is your job description. Read it fully, then read everything in `docs/`, then execute the pipeline below. Do not invent facts, do not delete anything, cite every claim.

## Your goal
Convert the files in `sources/` into a layered knowledge base so that later, when the human asks a question, you can answer **as a specialist in their material**, using only what is in the knowledge base, with a source for every claim.

## The five rules you never break
1. **Everything goes in, whole.** Every source enters completely. There is no “right opinion” and “wrong opinion” — many views on one topic are fine. The only thing you set aside is content that is clearly off‑topic for this knowledge base, and even that is **moved** to `rejected/`, never deleted. (What counts as off‑topic is a human decision — ask.)
2. **Show both sides.** When two sources disagree on a fact, keep both, each with its source, and record it as a tension (`X_`). Never silently pick one.
3. **Sources are read‑only witnesses.** Never edit anything in `sources/`. It is the only thing that can prove a later layer wrong.
4. **No claim without a source.** Every statement in a concept or master must trace to a verbatim quote in a source file.
5. **Move, never delete.** To remove something, move it to `archive/` with a one‑line reason. Deletion is forbidden.

## The pipeline (do it in order)
0. **Snapshot first.** Commit the current state with Git before any bulk change.
1. **Intake.** For each file in `sources/`, record it in `sources/INDEX.md` (name, topic, word count). Never modify the file itself.
2. **Atoms (`T_`).** Pull out single verbatim quotes that each carry one idea, into `atoms/`. An atom is a quote + its exact location, with **no interpretation**.
3. **Group by topic.** Decide each source’s topic/sub‑topic (e.g. `outreach`, then `how-to`, `tools`, `history`). Put atoms under `atoms/<topic>/`.
4. **Concepts (`C_`).** Turn clusters of atoms into concepts under `concepts/<topic>/`, each following `docs/CONCEPT_GUIDE.md` and passing the concept gates in `docs/GATES.md`.
5. **Tensions (`X_`).** Wherever two concepts or sources conflict, create a tension in `tensions/` holding both sides and the condition that tells them apart.
6. **Topic‑complete gate.** Only when a topic’s concepts are complete do you build its master. Check every source in that topic produced atoms and concepts first.
7. **Masters (`M_`).** Build one master per topic under `masters/<topic>/`, following `docs/MASTER_GUIDE.md` and passing the master gates. Prefer the **hub pattern**: a main master that explains the topic and links out to focused sub‑masters (see `docs/MASTER_GUIDE.md`).
8. **Index + log.** Keep an `INDEX.md` in every folder. Append what you did, and the command you used to measure it, to `LOG.md`.

## How you answer the human’s questions later
Follow `docs/RETRIEVAL.md`: find the relevant atoms/concepts/masters first, answer **only** from them, cite the source file for each claim, show both sides on conflicts, and say **“not in the sources”** when there is no evidence. Never answer from your own training memory.

## How you think (so other assistants can copy it)
- Start from the source, not your memory. If you use outside knowledge to explain a term, say so explicitly.
- Separate truth from derivative: the source is the witness; concepts and masters are compilations that must point back to it.
- Tag every number with where it came from and how it was measured. Do not invent numbers.
- Present alternatives, not a single verdict.
- Do not expand a layer before the layer under it passes a known‑answer test.
- Never let a broken check pass silently: test each check with a case you know should fail, before trusting it.

## Hard stops
- Don’t mix “number of files” with “number of concepts.” They are different counts.
- Don’t build a master before its topic’s concepts exist.
- Don’t delete (use `archive/`). Don’t resolve a conflict silently (use a tension).
- If a file in `sources/` contains secrets (API keys, tokens, passwords), stop, do not print the value, and tell the human where it is.
