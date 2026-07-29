---
name: understand
description: Establish and obtain approval for a software issue's need, scope, acceptance criteria, definition of done, exclusions and stakeholder record. Use for new TenX work or when material evidence changes an approved alignment.
---

# Understand

Read [shared controls](../../references/controls.md) completely before acting. Resolve every relative link in this file from this SKILL.md's installed location per shared controls `Locating plugin files` (root = the directory containing this file's `skills/` folder; fallback: `find "$HOME/.claude/plugins" "$HOME/.codex" "$HOME/Library/Application Support/Claude" -name controls.md -exec grep -l "TenX controls" {} + 2>/dev/null | sort -V | tail -1`). An unreadable linked file is a hard stop: report and stop.

## Goal — CRITICAL

Agree the need, assigned deliverables, acceptance criteria, definition of done and exclusions.

## Work

1. Read the task and linked sources. The entry may be a tracker ticket, a written problem description, or a production incident; capture whichever evidence exists as sources — for a ticket, its state/timeline and linked and closing pull requests; for a production incident, the triggering alerts, logs and error reports. Inspect recent merged work, commits mentioning the issue, current code, tests and applicable deployment evidence. Reconcile parent/children, docs and prior decisions; no source has automatic authority.
2. Classify every stated criterion as `unmet`, `partially met`, `satisfied` or `unclear`, with current-base evidence. Separate required outcomes from suggestions and follow-ups. Prove at least one required criterion is unmet.
3. If all required criteria are satisfied, stop before branches, edits, tracker writes or pull requests. Report resolving evidence and ask whether to close or update the tracker.
4. Record beneficiary, outcome and assigned portion. For partial work, split mixed requirements and record contracts, handoffs, exclusions and portion-scoped done.
5. Facts are looked up; decisions belong to the user. Resolve an unknown from evidence only when a specific artifact (file, migration, doc, prior decision) uniquely determines the answer; cite that artifact in the ledger. Everything else is the user's decision: put each one to them singly — one question per message (asking several at once is bewildering), with your recommended answer and concrete options where they exist, via the harness's question tool when available — then stop and wait for the reply. Never answer your own question: a self-resolved decision without uniquely-determining evidence is a fabricated decision. Continue until every material unknown is resolved, excluded or covered by an authorised interim rule. An unknown is material only when resolving it changes the drafted requirements, acceptance criteria, definition of done, exclusions or rollout.
6. Keep a ledger of question, resolver (the cited artifact, or the user's reply quoted verbatim), resolution and wrong-answer impact. For external decisions add owner, dependent/independent work and re-entry. If empty, record `Questions: None` with evidence.
7. Exclude externally dependent work unless the user supplies an interim rule and safe rollout. Mark provisional decisions with owner and re-entry.
8. Build the record from `<root>/references/templates/understand.md` and persist it per shared controls (`.tenx/<issue-id>/understand.md`), mirrored to the shared tracker once approved — approval grants tracker writes for this issue.
9. Stop and request explicit approval of the exact record revision, showing the persisted file's path and `shasum -a 256` digest in the same message — a request without them is invalid. After approval, write `understand.approval.md` from the approval template and show it. A named parent issue later receives one child ticket per approved slice in the shared tracker; if no suitable parent exists, propose one.

## Evidence

Current-state audit; criterion classification; reconciled sources; record revision/location; complete ledger; quoted approval.

## Gate — CRITICAL

Pass only with an approved exact persisted record, at least one currently unmet required criterion, no unresolved in-scope material unknown and external blockers excluded or provisionally resolved. Changed alignment or current-state evidence returns here.
