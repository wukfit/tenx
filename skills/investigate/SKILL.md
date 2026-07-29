---
name: investigate
description: Prove the smallest safe implementation path for an exact approved TenX alignment. Use after Understand approval, or when implementation reveals a new behavior class, caller, invariant, unsafe state or material design contradiction.
---

# Investigate

Read [shared controls](../../references/controls.md) completely before acting. Resolve every relative link in this file from this SKILL.md's installed location per shared controls `Locating plugin files` (root = the directory containing this file's `skills/` folder; fallback: `find "$HOME/.claude/plugins" "$HOME/.codex" "$HOME/Library/Application Support/Claude" -name controls.md -exec grep -l "TenX controls" {} + 2>/dev/null | sort -V | tail -1`). An unreadable linked file is a hard stop: report and stop. Require the exact approved Understand record: verify `.tenx/<issue-id>/understand.md` against `understand.approval.md` per shared controls and quote the approval verbatim in your phase-entry statement; missing, mismatched or unquotable returns to Understand. Request detail is never a record; "approved alignment from the incident context/request/prompt" is always an error.

## Goal — CRITICAL

Prove the smallest safe implementation path satisfying the approved alignment.

## Work

1. Reconfirm an approved unmet criterion on the exact current base. If none remains, return to Understand and take the no-work exit.
2. Trace behavior end-to-end: all callers, tests, contracts, persistence, deployment and owners. Compare dormant or old code with current rules.
3. Inspect and cite repository conventions before specifying migrations, identifiers, endpoint shapes, pagination, sorting, generated files or utilities. Reuse existing seams.
4. For persistence changes, establish historical behavior. Prove why existing immutable context cannot identify the record before adding stored identity or relationships. Reject designs justified only by unsupported state transitions.
5. Decide whether a toggle is needed. Protect changed or hidden production behavior; avoid toggles for safe additive behavior unless policy requires one.
6. Build a matrix of applicable operations, states, variants, trust failures, history, sibling callers and removal/retry/refund/rollback/dependency failures. Each cell names preserved behavior, an acceptance test, an evidenced exclusion or a blocked decision.
7. Map every criterion and invariant to its seam, callers, persistence/contract impact and named test or command.
8. Record facts separately from inferences, review/conflict/rollout risks, safe intermediate states and the minimum path.
9. Independently review for missing behaviors, callers, invariants, history, unsafe states, unsupported assumptions and simpler safe seams.
10. Persist the investigation record from its template as `.tenx/<issue-id>/investigate.md` and show its path and digest. The Gate passes on the independent `PASS` — the reviewer's verbatim output persisted from the review template as `review-investigate-r<N>.md`, embedding the reviewed record's digest — without user approval; present the record and stop only on user request, a hard stop, or an unresolved material unknown.

## Evidence

Approved record revision/location and quoted approval; exact source/base manifest; paths, symbols and callers; matrix; acceptance map; full review history and matching `PASS`.

## Gate — CRITICAL

Pass only with an independent `PASS` for the exact record revision and no material unknown. Contradiction returns here; changed alignment returns to Understand.
