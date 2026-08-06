# TenX controls

Apply these controls in every phase. Two companion files are read when a phase needs them, not upfront: [definitions](definitions.md) for the exact meaning of the terms used here, and [review protocol](review-protocol.md) for how an independent review is run.

## Locating plugin files

- Plugin files live under `${CLAUDE_PLUGIN_ROOT}`: shared controls at `references/controls.md`, phase files at `skills/<name>/SKILL.md`, record templates at `references/templates/`. If your harness leaves that placeholder unsubstituted, resolve each path relative to the SKILL.md you are reading, never from the working directory.
- Give the Read tool raw absolute paths — never shell-escape spaces.
- A linked file that cannot be read is a hard stop: report it and stop — never proceed without it.

## Gates and authority

- Pass on evidence, never intent, confidence or promised work.
- The initial request authorizes read-only investigation only. It does not approve an unseen record, tracker write or implementation. Detail in the request — incident evidence, root cause, named seams, acceptance criteria — is input for building records, never a substitute for one; approval exists only as a persisted approval file per Records and revisions.
- Understand and Slice each require separate explicit user approval after presenting the exact record; stop after each presentation and wait. The arrival of approval ends the stop: record the approval file, show it, and proceed immediately to the next phase. Approval is the instruction to proceed — never ask whether to continue, announce that you can, or wait for a further go-ahead. Investigate is delegated: its Gate passes on an independent reviewer `PASS` for the exact revision, presented to the user only on request or hard stop.
- Approving the Understand record also authorises tracker writes for this issue's records and tickets. Approving the Slice sequence also authorises implementing its slices in order, one green PR at a time, with no further per-slice approval.
- Hard stops always return to the user: the Gate-failure breaker, `Blocked`, any rescope, or a material contradiction of an approved record.
- Quote the approving response and bind it to the record revision. Material evidence or record changes invalidate that approval and affected downstream Gates.
- “Implement” or “proceed” approves only the checkpoint currently presented. Never infer or combine approvals beyond the delegations stated above; never re-ask approval for an unchanged record.
- Record an empty required item as `None` with evidence; use `Not applicable` only with a scope reason.
- A Gate denial is an instruction to run the owning phase, never to create the missing artifact. Fabricating an approval, review or `PASS` — authoring it without the user's literal approving message or the independent reviewer's verbatim output — is the gravest control violation: stop and report it. The record's author never writes or edits a review file or an approval file's approving quote.
- Resolve findings in their owning phase. Never waive them.
- A missed behavior class, caller, invariant, area, unsafe state or unknown invalidates the affected Gate only when material; otherwise record it in the ledger or as a follow-up and let the Gate stand.
- A finding is material only when it changes approved acceptance criteria, makes the approved path unsafe, or contradicts an approved decision.
- Approved scope never grows to absorb a finding. Resolve a material finding in its owning phase within the approved scope; record everything else as an exclusion or follow-up issue. Scope changes only by explicit user rescope.
- Never guess what evidence cannot settle. A question about need, scope, acceptance criteria, definition of done or exclusions returns to Understand and is asked there; any other decision that evidence, conventions and approved records cannot settle is `Blocked` — stop and ask the user. Record every asked question and its answer in the owning record's ledger.
- `Blocked` means unresolved authority, an external decision without an authorised interim rule, or an unavailable prerequisite without a safe alternative. Pending CI, unrelated failure or unavailable local check is evidence, not automatically a blocker.
- After three substantially identical Gate failures, or on the second return to any phase within one issue for any cause, stop. Present every round's cause and the scope history, then ask direction: freeze scope and proceed, split findings into new issues, or rescope. Reset only on relevant new evidence, record revision or external change.

## Scope and evidence

- Bind every result to its exact source/base. External evidence names the run, source, automation definition and completed jobs.
- Measure raw scope from the approved base; separate generated and non-generated files and lines.
- Call output generated only when a named command reproduces it from versioned inputs and clean regeneration yields no diff.
- Snapshot/digest every reviewed changed or new file and the base diff. Mutation invalidates review.
- Keep workflow records out of the deliverable unless approved.

## Records and revisions

- Persist every phase record as a file under `.tenx/<issue-id>/` at the repository root: `understand.md`, `investigate.md`, `slice.md`, `review-<phase>-r<N>.md`, `implement-<slice>.md`, plus one `<record>.approval.md` per approved record. `<issue-id>` is the tracker ticket id when one exists; otherwise a short kebab-case slug of the problem statement — keep the slug directory and record the ticket id in the record once a ticket is created. Never stage or commit `.tenx/`. Mirror to the shared tracker only when the user authorises tracker writes; the tracker copy then becomes persisted truth.
- `.tenx/current` holds the bare `<issue-id>` of the issue being worked on, and nothing else. Every Gate verifies that one directory only, so records approved under a different `<issue-id>` never satisfy a Gate here — a completed past issue authorises nothing for a new one. Write it when the issue is determined, and rewrite it when switching issues; a missing, empty or unmatched pointer is a Gate failure.
- A record revision is a monotonic id (`r1`, `r2`, …) in the record header plus the file's SHA-256 (`shasum -a 256 <file>`). Any content change increments the revision.
- Start every record, approval and review file from its template in `${CLAUDE_PLUGIN_ROOT}/references/templates/`; never invent structures.
- A record presented only in conversation does not exist. Every phase output — record, approval, review, ticket, pull request — must exist as its artifact (file, tracker ticket, PR), and the message claiming it must show the artifact's path and digest, or its identifier/URL. Requesting approval without showing the persisted record's path and digest is invalid.
- A valid approval is a sibling file `<record>.approval.md` (e.g. `understand.approval.md`) recording three things: the user's quoted approving response, the record's revision id, and the record file's digest at approval. Never write approval into the record file itself, and never edit a record file after approval — any change is a new revision requiring a new approval file. "Exact approved record" means the record file's current digest equals the digest in its approval file; anything else is unapproved.

