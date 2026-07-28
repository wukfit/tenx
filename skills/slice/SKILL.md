---
name: slice
description: Turn an exact approved TenX investigation into user-approved cohesive, reviewable, independently mergeable and deployable slices. Use after Investigate approval or when implementation scope grows semantically.
---

# Slice

Read [shared controls](../../references/controls.md) completely before acting. Resolve every relative link in this file from this SKILL.md's own installed location, never from the working directory (fallback: `find ~/.claude/plugins -path '*/tenx/*' -name controls.md | sort -V | tail -1`, or the equivalent plugin install root in other harnesses). A linked file that cannot be read is a hard stop: report it and stop — never proceed without it. Require and verify the exact approved Understand record with quoted approval and the exact Investigate record with its independent `PASS` — read the files under `.tenx/<issue-id>/`, recompute digests, match them against `understand.approval.md` and the Investigate review `PASS`, and quote both verbatim in your phase-entry statement; if you cannot quote them, or a file is missing or mismatched, return to the missing or changed phase. Request detail is never a substitute for a record.

## Goal — CRITICAL

Agree reviewable, mergeable and deployable deliverables.

## Work

1. Propose the smallest safe slices. Prefer interface contracts across ownership boundaries and inert additive seams before activation.
2. For each slice record outcome/criteria, repository/system, expected modules/files, generated/non-generated estimates and command, verification, exclusions, safe intermediate state and re-entry.
3. Classify every dependency separately as development, merge, deployment or activation. Require evidence for each; do not infer one from another. Never stack pull requests: every slice branches from and targets the default branch, and a slice depending on another slice's code is blocked from implementation until that slice is merged. An inert contract or stub is independent unless evidence proves otherwise.
4. Keep one cohesive outcome or seam with its tests. Eight non-generated files or 400 changed non-generated lines are warnings, not limits or targets. Never split implementation from tests, create test-only bookkeeping slices or reshape code to hit counts.
5. For a larger slice, explain why it is the smallest coherent unit and compare reasonable splits. Judge semantic breadth, coupling, repetition and reviewability; mechanical refactors may legitimately touch many files.
6. Persist the sequence as `.tenx/<issue-id>/slice.md` and show its path and digest. Independently review decomposition, coupling, size, dependency classes, order, deployment states and independent merge/deploy safety; persist the review as `review-slice-r<N>.md`.
7. Present the sequence, then stop and request its separate explicit approval. On approval (tracker writes were granted with the Understand approval), write `slice.approval.md`, then create/link the parent and one child ticket per slice in the shared tracker (in the owning project or repository), including outcome, criteria, dependencies, safety, expected scope, verification and exclusions — and show the created ticket identifiers or URLs in your message. If no tracker tool is available, that is `Blocked`: ask the user. Approval without the tickets shown is an unfinished phase.

## Evidence

Approved sequence revision/location and quoted approval; raw/generated estimates; dependency classification; full review history, resolutions and matching `PASS`.

## Gate — CRITICAL

Pass only when the user approves the exact independently passed sequence and every slice is cohesive, reviewable and independently mergeable/deployable under its recorded prerequisites.
