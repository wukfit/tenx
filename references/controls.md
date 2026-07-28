# TenX controls

Apply these controls in every phase.

## Gates and authority

- Pass on evidence, never intent, confidence or promised work.
- The initial request authorizes read-only investigation only. It does not approve an unseen record, tracker write or implementation. Detail in the request — incident evidence, root cause, named seams, acceptance criteria — is input for building records, never a substitute for one; approval exists only as a persisted approval file per Records and revisions.
- Understand and Slice each require separate explicit user approval after presenting the exact record; stop after each presentation. Investigate is delegated: its Gate passes on an independent reviewer `PASS` for the exact revision, presented to the user only on request or hard stop.
- Approving the Understand record also authorises tracker writes for this issue's records and tickets. Approving the Slice sequence also authorises implementing its slices in order, one green PR at a time, with no further per-slice approval.
- Hard stops always return to the user: the Gate-failure breaker, `Blocked`, any rescope, or a material contradiction of an approved record.
- Quote the approving response and bind it to the record revision. Material evidence or record changes invalidate that approval and affected downstream Gates.
- “Implement” or “proceed” approves only the checkpoint currently presented. Never infer or combine approvals beyond the delegations stated above; never re-ask approval for an unchanged record.
- Record an empty required item as `None` with evidence; use `Not applicable` only with a scope reason.
- Resolve findings in their owning phase. Never waive them.
- A missed behavior class, caller, invariant, area, unsafe state or unknown invalidates the affected Gate only when material; otherwise record it in the ledger or as a follow-up and let the Gate stand.
- A finding is material only when it changes approved acceptance criteria, makes the approved path unsafe, or contradicts an approved decision.
- Approved scope never grows to absorb a finding. Resolve a material finding in its owning phase within the approved scope; record everything else as an exclusion or follow-up issue. Scope changes only by explicit user rescope.
- Never guess what evidence cannot settle. A question about need, scope, acceptance criteria, definition of done or exclusions returns to Understand and is asked there; any other decision that evidence, conventions and approved records cannot settle is `Blocked` — stop and ask the user. Record every asked question and its answer in the owning record's ledger.
- `Blocked` means unresolved authority, an external decision without an authorised interim rule, or an unavailable prerequisite without a safe alternative. Pending CI, unrelated failure or unavailable local check is evidence, not automatically a blocker.
- After three substantially identical Gate failures, or on the second return to any phase within one issue for any cause, stop. Present every round's cause and the scope history, then ask direction: freeze scope and proceed, split findings into new issues, or rescope. Reset only on relevant new evidence, record revision or external change.

## Independent planning review

When a phase requires it:

1. Use a reviewer who neither authored the record nor will implement it.
2. Provide read-only exact sources, approved records and consulted-source manifest. Require independent source/caller enumeration, manifest corrections and every named probe without leading findings.
3. Persist full output, reviewer/run identity, input/source digests, probe answers, findings and owning-phase routing.
4. Resolve findings and rerun the same reviewer until it rechecks every prior finding and returns `PASS` for the exact revision. A replacement receives the full history and re-verifies everything. Never discard an unfavourable review.
5. A record change invalidates its verdict. No reviewer means Gate failure. Review validates evidence; it stands in for user approval only where these controls delegate a Gate (Investigate), never elsewhere.

## Scope and evidence

- Bind every result to its exact source/base. External evidence names the run, source, automation definition and completed jobs.
- Measure raw scope from the approved base; separate generated and non-generated files and lines.
- Call output generated only when a named command reproduces it from versioned inputs and clean regeneration yields no diff.
- Snapshot/digest every reviewed changed or new file and the base diff. Mutation invalidates review.
- Keep workflow records out of the deliverable unless approved.

## Records and revisions

- Persist every phase record as a file under `.tenx/<issue-id>/` at the repository root: `understand.md`, `investigate.md`, `slice.md`, `review-<phase>-r<N>.md`, `implement-<slice>.md`, plus one `<record>.approval.md` per approved record. `<issue-id>` is the tracker ticket id when one exists; otherwise a short kebab-case slug of the problem statement — keep the slug directory and record the ticket id in the record once a ticket is created. Never stage or commit `.tenx/`. Mirror to the shared tracker only when the user authorises tracker writes; the tracker copy then becomes persisted truth.
- A record revision is a monotonic id (`r1`, `r2`, …) in the record header plus the file's SHA-256 (`shasum -a 256 <file>`). Any content change increments the revision.
- A valid approval is a sibling file `<record>.approval.md` (e.g. `understand.approval.md`) recording three things: the user's quoted approving response, the record's revision id, and the record file's digest at approval. Never write approval into the record file itself, and never edit a record file after approval — any change is a new revision requiring a new approval file. "Exact approved record" means the record file's current digest equals the digest in its approval file; anything else is unapproved.

## Definitions

Use these meanings exactly; do not reinterpret.

- Shared tracker: the project's issue system (GitHub Issues, Jira, Linear, Azure Boards, …). Determine it once per issue, in order: the user's statement, where the issue itself lives, repository/project configuration, tracker tools connected to the session. If still unknown, ask the user once and record the answer in the Understand record.
- Forge: the code host serving pull/merge requests (GitHub, GitLab, Bitbucket, …). Determine it from `git remote get-url origin`; if unrecognized, ask the user.
- Substantially identical Gate failures: same Gate and same root cause.
- Semantic growth: the work delivers an outcome, behavior class or seam not named in the approved slice record. File or line count variance alone is never semantic growth.
- Cohesive slice: one outcome or seam plus its tests; nothing else.
- Inert: merged code unreachable in production — uncalled, unrouted, or behind a default-off toggle.
- Safe intermediate state: after this slice alone merges and deploys, every existing behavior is preserved and no partial feature is user-reachable.
- Drift: post-approval changes on the current base touching the approved files, symbols, callers or invariants; apply the materiality test to decide whether it invalidates.
- Independent reviewer: a fresh-context sub-agent or sub-task (in Claude Code, the Agent tool; otherwise the harness's sub-task facility, or a fresh session) given only the listed inputs and none of the author's working context or conclusions.
- Canonical aggregate: the repository's documented full verification command or CI aggregate job; never an ad-hoc subset.
- Cold review: reviewing the complete diff in fresh context, not from memory of having written it.
