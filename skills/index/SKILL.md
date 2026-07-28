---
name: index
description: Route broad TenX software-delivery requests to Understand, Investigate, Slice or Implement. Use when the user asks to use TenX, deliver an issue through TenX, continue TenX work, or is unsure which TenX phase applies.
---

# TenX

Read [shared controls](../../references/controls.md) completely.

Phase records exist only as files under `.tenx/<issue-id>/` (or their authorised tracker mirror). List that directory before selecting a phase. The request prompt is never a record: however detailed — incident evidence, root cause, required behavior, acceptance criteria — it is input to Understand, not an approval, an investigation or a slice. "Deliver", "fix" or "implement" in the request authorizes entering the process, never skipping phases.

Select the earliest phase whose entry evidence is satisfied:

1. [Understand](../understand/SKILL.md): `.tenx/<issue-id>/understand.md` with a valid approval header (quoted user response, revision id, matching digest) does not exist.
2. [Investigate](../investigate/SKILL.md): approved `understand.md` exists, but no `investigate.md` whose review history ends in `PASS` for its current digest.
3. [Slice](../slice/SKILL.md): approved `understand.md` and PASS-reviewed `investigate.md` exist, but no `slice.md` with a valid approval header.
4. [Implement](../implement/SKILL.md): all three records verify by digest and one slice from the approved sequence is selected — Slice approval is the implementation authority.

Never reconstruct missing approval from intent, summaries, request detail or later work. If evidence changed, return to its owning phase. State the selected phase, the record files checked and their digest results, then read and follow that phase file completely. Load no later phase early.
