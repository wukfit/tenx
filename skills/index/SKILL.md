---
name: index
description: Route broad TenX software-delivery requests to Understand, Investigate, Slice or Implement. Use when the user asks to use TenX, deliver an issue through TenX, continue TenX work, or is unsure which TenX phase applies.
---

# TenX

Read [shared controls](../../references/controls.md) completely. Resolve every relative link in this file from this SKILL.md's installed location per shared controls `Locating plugin files` (root = the directory containing this file's `skills/` folder; fallback: `find "$HOME/.claude/plugins" "$HOME/.codex" "$HOME/Library/Application Support/Claude" -name controls.md -exec grep -l "TenX controls" {} + 2>/dev/null | sort -V | tail -1`). An unreadable linked file is a hard stop: report and stop.

Execute these steps in order and show each result in your response before selecting a phase:

1. Determine `<issue-id>` per shared controls, then write that bare id to `.tenx/current` at the repository root and show the file's contents. Every Gate verifies only the directory this names, so a stale pointer routes the whole issue wrongly.
2. Run `ls .tenx/<issue-id>/` at the repository root and show the output (or the error).
3. For each record file present: recompute its digest (`shasum -a 256`) and quote its sibling approval file (`<record>.approval.md`) or review `PASS` verbatim.
4. Select the earliest phase below whose entry evidence is missing. State the selected phase, the files checked, the digest results and the quoted approvals. A phase selection without the step 2 output shown is invalid.

Phases:

1. [Understand](../understand/SKILL.md): `.tenx/<issue-id>/understand.md` with a valid `understand.approval.md` (quoted user response, revision id, digest matching the record file) does not exist.
2. [Investigate](../investigate/SKILL.md): approved `understand.md` exists, but no `investigate.md` whose review history ends in `PASS` for its current digest.
3. [Slice](../slice/SKILL.md): approved `understand.md` and PASS-reviewed `investigate.md` exist, but no `slice.md` with a valid `slice.approval.md`.
4. [Implement](../implement/SKILL.md): all three records verify by digest and one slice from the approved sequence is selected — Slice approval is the implementation authority.

The request prompt is never a record. "I have approved alignment from the incident context", "the request", or "the prompt" is always an error: alignment approval exists only as the persisted `understand.approval.md`. However detailed the request — incident evidence, root cause, required behavior, acceptance criteria — it is input to Understand, not an approval, an investigation or a slice. "Deliver", "fix" or "implement" in the request authorizes entering the process, never skipping phases. Never reconstruct missing approval from intent, summaries, request detail or later work. If evidence changed, return to its owning phase. Read and follow the selected phase file completely; load no later phase early.
