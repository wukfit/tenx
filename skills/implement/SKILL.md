---
name: implement
description: Implement, self-review, ship and monitor one exact approved TenX slice. Use only when approved Understand and Slice records and a PASS-reviewed Investigate record exist and one slice from the approved sequence is selected.
---

# Implement

Read [shared controls](../../references/controls.md) completely before acting. Resolve every relative link in this file (including the bundled quality-gate, commit-changes, ship-changes and pr-review-responder skills) from this SKILL.md's installed location per shared controls `Locating plugin files` (root = the directory containing this file's `skills/` folder; fallback: `find "$HOME/.claude/plugins" "$HOME/.codex" "$HOME/Library/Application Support/Claude" -name controls.md -exec grep -l "TenX controls" {} + 2>/dev/null | sort -V | tail -1`). An unreadable linked file is a hard stop: report and stop.

Require the exact approved Understand and Slice records, the PASS-reviewed Investigate record, and one slice selected from the approved sequence — Slice approval is the implementation authority. Before anything else, verify all three under `.tenx/<issue-id>/` per shared controls and quote the approval files verbatim in your phase-entry statement; any missing, mismatched or unquotable artifact: stop and route via [index](../index/SKILL.md), never proceeding on request detail. Then verify issue state, ownership, current default branch and material drift. Unchanged handoff records remain approved; changed evidence returns to its owning phase.

## Goal — CRITICAL

Deliver one approved slice without drift and publish a human-review-ready pull request with green automation.

## Implement

1. Confirm the work is unowned; assign only with authority. Use the correct base, one branch and repository rules.
2. For behavior, work one test at a time: add the failing acceptance test, capture command/output against the pre-implementation checkpoint, write minimum code, then refactor green. Never weaken tests. If the acceptance test cannot be made to fail against the current base, that is a material contradiction: stop as `Blocked` and ask the user — never drop, weaken or defer the criterion silently.
3. For non-behavior work, capture equivalent evidence such as apply/rollback, generated-contract diff or infrastructure plan.
4. After each cycle compare behavior, callers, files/modules and invariants with approved records. Record unrelated follow-ups. A material new behavior class or design contradiction returns to Investigate with scope held constant; semantic slice growth is stripped back to the approved slice and recorded as a follow-up unless the approved outcome is unreachable without it, which returns to Slice.
5. Run focused checks and exact local equivalents of affected automation jobs selected from their entrypoints, modules, selectors and config.
6. Run the canonical aggregate. Never substitute defaults that omit configured suites, generated checks or contracts. If none exists, run every automation verification job.
7. Compare actual scope and clean regeneration with estimates. Count variance alone does not invalidate Slice; semantic growth does.

### Evidence

Acceptance-to-test map; red/equivalent checkpoints; focused, affected and aggregate results bound to source; raw/generated scope; regeneration; approved-only diff.

### Gate — CRITICAL

Pass when every acceptance criterion maps to a named test with a captured red (failing) run against the pre-implementation checkpoint and a green run after — a new test in the shipped diff, or an existing test only if that captured red run shows it failing before the change. An always-green test proves nothing and never satisfies a criterion; if no test can go red on the current base, that is the `Blocked` contradiction above. Additionally: change-relevant criteria and checks pass, unavailable or unrelated failures are evidenced, and actual behavior remains the approved cohesive slice.

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

1. Read and follow the bundled [commit-changes](../commit-changes/SKILL.md) and [ship-changes](../ship-changes/SKILL.md) files. Never substitute the harness's default commit, branch or PR flow: a harness-generated PR body (e.g. a `## Summary`/`## Test plan` checklist) or auto-named branch left in place is an error. Prefer the project PR template when one exists; otherwise ship-changes' problem/solution body. Every claim in the PR body must name its evidence in the shipped diff or a captured command output; no unbacked claims or checkmarks. Keep commits focused and separate generated churn when useful.
2. Creating the pull request is a required deliverable of this phase; "do not merge" is not "do not create". Never merge.
3. The shipped tree/base diff must match the reviewed snapshot. Mutation reruns Implement verification and Self-review.
4. Monitor required checks on the latest commit until terminal. Never call pending, queued, unexpected skipped, cancelled or failing checks green. Debug caused failures. For an unrelated, pre-existing or flaky failure, capture evidence and rerun the unchanged job once; a substantially identical second failure needs user direction or external repair. “Unrelated” is not “green.”
5. Use the bundled [pr-review-responder](../pr-review-responder/SKILL.md) only when requested.

### Gate — CRITICAL

Pass only when every required check on the latest commit is green and the PR is ready for human review.

Implement has exactly three terminal states: this Gate passed; `Blocked`, reported with its blocking evidence; or a return to an owning phase. "Done except <skipped step>" is not a state — reporting completion while any required step (aggregate, self-review, PR creation, check monitoring) was skipped without `Blocked` evidence is a false completion report.

## Next slice and parallel work

Start the next slice in a fresh task after the prior merge, unless explicit parallel-development approval exists. Never stack pull requests: every slice branches from and targets the current default branch. A slice depending on an unmerged slice's code is blocked from implementation until that slice merges; record the blocking slice, merge prerequisite, deployment prerequisite and re-entry. A genuinely independent slice may be developed and its PR created in parallel even when deployment or activation must wait.

At handoff, pass exact record revisions, approvals, current base, scope, exclusions, dependencies, verification and re-entry rules. The destination verifies drift but does not re-request approval for unchanged records. Start blocked work only after proven re-entry.
