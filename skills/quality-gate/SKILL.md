---
name: quality-gate
description: Use when preparing, self-reviewing, or sanity-checking changes before PR creation, automated review, human review, merge, or after repeated review comments about tests, UI state, async lifecycle, data ordering, observability, contracts, security, privacy, production safety, docs, or source provenance.
---

# Quality Gate

## Overview

Run an evidence-backed pre-PR quality gate for software changes. The lead agent owns scope, repository convention discovery, mechanical scans, subagent dispatch, de-duplication, and final classification; bucket agents provide focused semantic review.

This skill is intentionally generic. Repo-specific commands, domain invariants, generated-file rules, privacy expectations, and review scars should live in the repository and be read as part of the gate.

## Lead Workflow

1. Read applicable repo instructions and the issue/PR/spec the branch claims to satisfy:
   - `AGENTS.md`, `CLAUDE.md`, or equivalent agent instructions.
   - Repo-owned convention guides linked from those files, such as `docs/guides/conventions.md`, `docs/guides/review-readiness.md`, or project-specific paths.
   - PR metadata, issue acceptance criteria, design docs, or implementation plans.
2. Establish diff scope:
   - Prefer `git diff --stat <base>...HEAD` and `git diff --name-only <base>...HEAD` against the repo's default branch (`origin/main` when it exists; otherwise the ref the mechanical scan reports as its base).
   - Include unstaged/staged changes when reviewing local work before PR creation.
   - If reviewing an existing PR, fetch PR metadata, comments, and unresolved review threads.
3. Run the mechanical scan using the scripts bundled with this skill (`<skill-dir>` is the directory containing this SKILL.md):

```bash
python3 <skill-dir>/scripts/quality_scan.py
python3 <skill-dir>/scripts/enumerations.py
```

   The scanner auto-detects the base branch (origin default, then `origin/main`, `origin/master`, `main`, `master`); pass `--base <ref>` to override. It fails loudly when an explicit base ref does not resolve — do not treat a zero-file scan as a pass. `enumerations.py` prints raw material (changed exported symbols with callers in unchanged files, permission-relevant added lines, new remote calls) for the Required Enumerations step — its output is table input, not findings.

4. Build the Required Enumerations (see section below). These are mandatory, deterministic, fill-in-the-table steps — not judgment calls. The lead may delegate rows to bucket agents but owns table completeness, and each table (or an explicit per-table "not applicable because ...") must appear in the final output.
5. Choose only relevant bucket agents from `references/bucket-prompts.md`. Do not dispatch all buckets for tiny changes.
6. Treat invocation of this skill as the request to use delegated bucket agents by default. Use parallel bucket agents when the PR spans independent risk areas; fall back to running bucket prompts sequentially in the lead agent only when subagents are unavailable or the user explicitly opts out.
7. Give each bucket agent raw context: issue/PR goal, repo conventions, changed file list, relevant diff excerpts, and mechanical-scan output. Do not give your suspected answers. Every dispatched bucket prompt must additionally contain numbered, task-specific probes derived from this diff (concrete files, symbols, grants, invariants to check) — never just the generic bucket text — and must instruct the agent to answer every numbered probe explicitly, where "no finding" for a probe requires stating what was checked. Require every finding to state severity, confidence (`high`/`medium`/`low`), `file:line`, the quoted added diff line(s) it rests on, and a minimal suggested fix or the exact test that would pin the behavior.
8. Run `Adversarial integration review` as a separate final bucket when required by the dispatch matrix. Give it the full diff context plus completed bucket outputs, and ask it to find plausible ways the PR is wrong. The lead agent must verify every adversarial claim before classifying it.
9. Require every selected bucket to complete before classifying it. If a bucket agent times out, fails, is shut down, or returns no usable result, restart that bucket once with the same current context. Absence of a bucket result is not evidence of absence of findings.
10. Integrate findings. Verify every `must fix` claim against the current diff before classifying it (the quoted lines must actually exist in the diff), and drop or downgrade findings tagged low confidence that lack quoted diff evidence:
   - `must fix`: correctness, data loss, unsafe production/privacy behavior, broken contract, missing critical test.
   - `should fix`: likely reviewer comment, brittle assumption, unclear behavior, weak diagnostics.
   - `explain`: verified false positive or intentional product/design choice.
   - `follow-up`: real issue split out because it is shared infrastructure or outside this PR.
   - `out of current slice`: real PR-surface issue that is outside the user's currently requested implementation slice.
   - `incomplete`: selected bucket did not complete after retry; treat as a gate gap, or as `must fix` when the missing bucket covers high-risk changed code.
11. Treat gate findings as review output, not implementation instructions. Report and classify findings before fixing them unless the user explicitly asked to fix all findings, or the finding is a clear `must fix` inside the exact implementation slice already approved. Ask before expanding scope.
12. Before declaring the PR ready, run focused tests/checks matching the risk and repo conventions.

## Required Enumerations

These convert the highest-yield review questions from judgment into enumeration. Each produces a table in the final output; an empty table must say why it is empty (for example "no exported symbol changed behavior"), never be silently omitted. `scripts/enumerations.py` prints raw material for E1, E2, and E4; it lists candidates, it does not decide.

- **E1 Blast radius.** For every exported function, method, class, or module whose observable behavior changed (not just whose signature changed), list ALL call sites — including files this PR does not touch, other packages/modules, background workers, serverless functions, and scripts — and classify each: `updated in this PR`, `unaffected (state why)`, or `affected and unhandled (finding)`. Re-exports (barrel files, facades, public headers) count as call sites and must be traced one level further. Sampling is not enumeration; if the caller list is truncated anywhere, say so.
- **E2 Capability parity.** Required whenever the PR adds access to an external resource (storage prefix, table, queue, API, secret) or changes permissions/roles/config in any platform's terms (cloud IAM, database grants, service accounts, API scopes). Table: each code path that newly reaches the resource x each runtime that executes that code (every independently deployed unit: each serverless function, service, app server, worker, script, scheduled job) x the grant or env/config evidence at `file:line`, or `MISSING`. A grant existing for one sibling runtime is not evidence for another. Also record which identity each runtime actually authenticates as (assumed role, service account, static keys, connection string) — a grant to an identity the runtime does not use is `MISSING` with a note.
- **E3 Invariant writers.** Quote the PR's core invariant verbatim from the PR description/RFC/issue (for example "rows stay under the size limit", "X is the source of truth"). List every OTHER writer and reader of the same rows, objects, keys, or state — changed or not — and mark each as upholding or violating the invariant. The most expensive bugs live in unchanged writers that the PR newly exposes.
- **E4 New-remote-read failure audit.** For every remote/network read or write this PR adds inside an existing endpoint, worker, or job: quote the enclosing catch/fallback handling its failure, or record `none — whole request/invocation fails`. Then compare siblings in the same diff: if two near-identical paths handle the same failure differently (one degrades, one hard-fails; one retries, one terminal-fails), either justify or flag the divergence.
- **E5 Doc-claims diff.** Required when docs and code change together. For every normative sentence in added/changed docs (contains "overwrites", "prefers", "guarantees", "must", "will", "grants", "falls back"), map it to code evidence at `file:line`: `agrees`, `disagrees (finding)`, or `not implemented (finding)`.

Cheap-green guard: if a PR over roughly 1000 changed lines touching infra, workers, or new storage yields zero `must fix` findings, treat the gate itself as suspect — re-run the adversarial bucket with E1–E3 as mandatory named probes before reporting, and say in Verification that the guard fired.

## Bucket Completion Rules

- A bucket can be marked passed only when it returns a completed result with either findings or an explicit no-findings statement.
- A bucket that leaves any numbered probe from its dispatch prompt unanswered is incomplete, even if it returned findings for other probes. Restart it once with the unanswered probes called out.
- If a bucket agent fails, times out, is interrupted, is shut down, or returns an unusable answer, restart the same bucket once with the same current diff context.
- If the retry also fails, do not say the gate passed. Report the bucket under `Verification` as incomplete and classify the overall gate as blocked when that bucket is required for correctness, production safety, privacy, lifecycle state, schema contracts, or data integrity.
- Final summaries must distinguish `passed`, `found issues`, and `incomplete` bucket states.

## Dispatch Matrix

| Changed area | Required buckets |
| --- | --- |
| Any code change (default row, always in scope) | correctness/logic, tests |
| UI components, CSS, navigation, feature flags | UI/state/accessibility, tests |
| Workers, jobs, senders, recordings, retries, timers | async/idempotency, observability, tests |
| Database/API/external reads, dates, latest/current/prior | data/order/bounds, contracts, tests, security when user/customer/patient boundaries or query construction change |
| API routes, validation schemas, persisted rows, generated declarations | contracts, tests, observability, security |
| Package manifests, dependency constraints, public exports | contracts, tests |
| Scripts touching production systems, exports, credentials, sensitive data | privacy/prod-safety, security, data/order/bounds, observability |
| Prompts, parsers, schemas, generated files, docs | contracts, docs/truthfulness, tests, security when model output can influence user-visible content, persistence, tools, or side effects |
| Markdown plans/RFCs/ADRs/PR description | docs/truthfulness |
| Auth/session, permissions, tenant/clinic boundaries, redirects, external fetches, uploads/files, HTML rendering, secrets/config, IAM/serverless config | security, contracts, privacy/prod-safety |

Run `Adversarial integration review` as a separate final agent when the PR spans three or more rows (not counting the default `Any code change` row), touches docs plus code, touches prompts plus parsing, touches schemas plus lifecycle/persistence, changes worker/sender side effects, changes external-provider integration, already received review comments, or is large enough that context compaction is likely. For tiny PRs, the lead may run the adversarial prompt inline, but it must still produce explicit "top ways this PR could be wrong" output.

If a PR spans three or more rows (excluding the default row), dispatch selected bucket agents in parallel by default when tools allow it. Keep the lead agent responsible for final judgment. If subagents are unavailable, run the same selected bucket prompts sequentially.

## Mechanical Scan Scope

The scanner catches cheap repeat issues that are mostly language-agnostic:

- non-portable docs: `/Users/...`, `~/Downloads`, `Desktop`, "this machine", local scratch/source wording
- credential-ish names in committed docs: concrete `api-key`, `secret`, `token`, `password`, or parameter names
- broad changed test names that may overclaim fixture/assertion coverage
- prompt/spec examples that appear to violate nearby declared output rules
- JSON-only/no-commentary prompts that include fenced examples or prose-like example output
- Markdown headings with adjacent duplicate words that suggest copy/paste drift
- merge conflict markers in added lines
- committed secret material in added lines (AWS/GitHub/Slack token formats, private key blocks)
- focused or skipped tests added in test files (`.only`, `fit`, `fdescribe`, `.skip`, `@pytest.mark.skip`)
- debug leftovers in added non-test code (`console.log`, `debugger`, `breakpoint()`, `pdb.set_trace`, `binding.pry`)
- `TODO`/`FIXME`/`HACK`/`XXX` introduced in added code lines

Mechanical findings are prompts for review, not automatic proof. Verify before fixing or dismissing.

## Output Shape

Return findings first, ordered by severity:

```text
Must fix
- [bucket] file:line (confidence) - issue, quoted added line, why it matters, and the minimal fix or pinning test

Should fix
- ...

Explain / intentional
- ...

Follow-up
- ...

Out of current slice
- ...

Required enumerations
- E1 blast radius / E2 capability parity / E3 invariant writers / E4 remote-read failure audit / E5 doc-claims diff — each as a table, a summary with counts, or an explicit "not applicable because ..."

Verification
- commands run, bucket states, pass/fail, any incomplete buckets or gaps, and whether the cheap-green guard fired

Reviewer-obvious objections
- top 3 plausible reviewer challenges considered, with the evidence that fixes, explains, or scopes each one
```

If there are no findings, say that clearly and name residual risks.

## Common Mistakes

- Do not turn gate findings into implementation work automatically; classify first, then fix only approved scope.
- Do not let bucket agents comment on unrelated files just because they are interesting.
- Do not accept automated-review claims without checking the current diff and repo helpers.
- Do not treat a missing, timed-out, failed, or shut-down bucket agent as a successful pass. Restart it once, then report it as incomplete if it still does not complete.
- Do not treat missing tests as a generic complaint; name the exact behavior or fixture shape that would have caught the regression.
- Do not skip the adversarial integration bucket just because the focused buckets passed; cross-surface contradictions are often invisible inside one bucket.
- Do not merge security into privacy/prod-safety. Privacy asks "could this expose or misuse sensitive data?"; security asks "can this be abused across a trust boundary?"
- Do not accept "backward compatibility" metadata claims unless the contract enforces them. For paired canonical/compatibility fields, verify parser, schema, declarations, and tests all preserve the invariant.
- Do not bury production safety, sensitive-data, or contract issues under nits.
- Do not create project docs wherever convenient; read repo instructions and use the documented project docs location.
- Do not treat resolved or outdated review threads as proof that an issue is gone; verify the final diff or target branch when the claim is easy to check.
- Do not treat a replied-but-unresolved review thread as done. Each thread should end as fixed, resolved intentional/explain, or split into a follow-up.
- Do not expand a narrow review-response or cleanup slice because the whole-PR gate found adjacent valid work; report it as `out of current slice` or `follow-up` unless the user chooses to expand scope.
- Do not accept bucket findings that lack quoted added-line evidence; verify them against the diff or drop them before reporting.
- Do not skip the correctness/logic bucket because a change is "just a utility or helper"; pure logic changes are exactly where copy-paste and boundary bugs hide, and the default dispatch row always applies.
- Do not sample where the skill demands enumeration. "I checked several callers" is not the E1 table; "the other workers got grants" is not the E2 table. Missing tables are a gate gap, not an implied pass.
- Do not assume a runtime has a permission because a sibling runtime got it in the same diff; every independently deployed bundle authenticates separately and gets its own E2 row.
- Do not review only the files in the diff. A PR that changes a shared function's behavior reviews every caller of that function; the diff defines what changed, E1 defines what to read.
- Do not dispatch a bucket with only the generic bucket prompt. A dispatch without diff-specific numbered probes produces generic reviews regardless of model quality.
