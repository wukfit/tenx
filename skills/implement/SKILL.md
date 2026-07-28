---
name: implement
description: Implement, self-review, ship and monitor one exact approved TenX slice. Use only when approved Understand and Slice records and a PASS-reviewed Investigate record exist and one slice from the approved sequence is selected.
---

# Implement

Read [shared controls](../../references/controls.md) completely before acting.

Require the exact approved Understand and Slice records with quoted approvals, the exact Investigate record with its independent `PASS`, and one slice selected from the approved sequence — Slice approval is the implementation authority. Verify issue state, ownership, current default branch and material drift. Unchanged handoff records remain approved; changed evidence returns to its owning phase.

## Goal — CRITICAL

Deliver one approved slice without drift and publish a human-review-ready pull request with green automation.

## Implement

1. Confirm the work is unowned; assign only with authority. Use the correct base, one branch and repository rules.
2. For behavior, work one test at a time: add the failing acceptance test, capture command/output against the pre-implementation checkpoint, write minimum code, then refactor green. Never weaken tests.
3. For non-behavior work, capture equivalent evidence such as apply/rollback, generated-contract diff or infrastructure plan.
4. After each cycle compare behavior, callers, files/modules and invariants with approved records. Record unrelated follow-ups. A material new behavior class or design contradiction returns to Investigate with scope held constant; semantic slice growth is stripped back to the approved slice and recorded as a follow-up unless the approved outcome is unreachable without it, which returns to Slice.
5. Run focused checks and exact local equivalents of affected automation jobs selected from their entrypoints, modules, selectors and config.
6. Run the canonical aggregate. Never substitute defaults that omit configured suites, generated checks or contracts. If none exists, run every automation verification job.
7. Compare actual scope and clean regeneration with estimates. Count variance alone does not invalidate Slice; semantic growth does.

### Evidence

Acceptance-to-test map; red/equivalent checkpoints; focused, affected and aggregate results bound to source; raw/generated scope; regeneration; approved-only diff.

### Gate — CRITICAL

Pass when change-relevant criteria and checks pass, unavailable or unrelated failures are evidenced, and actual behavior remains the approved cohesive slice.

## Self-review

Cold-review the diff for:

- criteria, exclusions, edges, callers, tests, generated output and toggle safety;
- consistent results, IDs, errors, diagnostics, side effects and tests for changed decisions;
- unnecessary exports/parameters, ignored inputs, placeholders, compatibility-sensitive errors and invalid fixtures;
- naming, responsibility, conventions, duplication, speculative flexibility and single-deliverable shape.

Run the bundled [quality-gate](../quality-gate/SKILL.md); its dispatch matrix decides the buckets. Classify every finding and fix only within the slice. A content fix reruns the full Implement Gate; a new problem class returns to Investigate or Slice. Record the reviewed snapshot/digests and follow-ups.

### Gate — CRITICAL

Pass with complete `quality-gate`, no incomplete bucket or in-scope finding, and one reviewable deliverable.

## Ship and monitor

1. Commit via the bundled [commit-changes](../commit-changes/SKILL.md) and ship via the bundled [ship-changes](../ship-changes/SKILL.md). Prefer the project PR template when one exists; otherwise use a terse problem/solution body. Keep commits focused, separate generated churn when useful, and never merge.
2. The shipped tree/base diff must match the reviewed snapshot. Mutation reruns Implement verification and Self-review.
3. Monitor required checks on the latest commit until terminal. Never call pending, queued, unexpected skipped, cancelled or failing checks green. Debug caused failures. For an unrelated, pre-existing or flaky failure, capture evidence and rerun the unchanged job once; a substantially identical second failure needs user direction or external repair. “Unrelated” is not “green.”
4. Use the bundled [pr-review-responder](../pr-review-responder/SKILL.md) only when requested.

### Gate — CRITICAL

Pass only when every required check on the latest commit is green and the PR is ready for human review. Never merge or start the next slice.

## Next slice and parallel work

Start the next slice in a fresh task after the prior merge, unless explicit parallel-development approval exists. Never stack pull requests: every slice branches from and targets the current default branch. A slice depending on an unmerged slice's code is blocked from implementation until that slice merges; record the blocking slice, merge prerequisite, deployment prerequisite and re-entry. A genuinely independent slice may be developed and its PR created in parallel even when deployment or activation must wait.

At handoff, pass exact record revisions, approvals, current base, scope, exclusions, dependencies, verification and re-entry rules. The destination verifies drift but does not re-request approval for unchanged records. Start blocked work only after proven re-entry.
