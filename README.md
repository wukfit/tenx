# TenX

Evidence-gated software delivery from stakeholder alignment through reviewed pull request.

TenX is a Claude Code plugin (also usable from the Codex plugin manifest). It splits delivery
into four phases and refuses to let an agent skip one. Each phase writes a record file, and each
gate checks that record's digest against a persisted approval or an independent review. Intent,
confidence and a detailed prompt never count as approval.

## Install

Add the marketplace, then install the plugin:

```bash
/plugin marketplace add wukfit/tenx
```

```bash
/plugin install tenx@wukfit
```

Then start work with the router skill:

```
Use TenX to deliver this issue.
```

## The four phases

| Phase | Skill | Produces | Passes when |
| --- | --- | --- | --- |
| Understand | `tenx:understand` | `understand.md` | The user explicitly approves the presented record |
| Investigate | `tenx:investigate` | `investigate.md` | An independent reviewer returns `Verdict: PASS` |
| Slice | `tenx:slice` | `slice.md` | The user explicitly approves the slice sequence |
| Implement | `tenx:implement` | `implement-<slice>.md`, a PR | One approved slice ships green |

`tenx:index` is the router. It reads `.tenx/current`, lists the issue's records, recomputes each
digest, and selects the earliest phase whose entry evidence is missing.

Approving Understand also authorises tracker writes for the issue. Approving the slice sequence
also authorises implementing those slices in order, one green PR at a time, with no further
per-slice approval.

## Records

Records live under `.tenx/<issue-id>/` at the repository root and are never committed
(`.tenx/` is gitignored). `<issue-id>` is the tracker ticket id when one exists, otherwise a
kebab-case slug of the problem statement.

```
.tenx/
  current                      # the bare <issue-id> being worked on
  <issue-id>/
    understand.md
    understand.approval.md     # quoted user approval + revision id + record digest
    investigate.md
    review-investigate-r1.md   # independent reviewer output, verbatim
    slice.md
    slice.approval.md
    implement-<slice>.md
```

An approval file records three things: the user's quoted approving response, the record's
revision id (`r1`, `r2`, …), and the record file's SHA-256 at approval. A record is "approved"
only while its current digest still matches. Editing an approved record creates a new revision
and invalidates the approval.

Templates for every record, approval and review file are in `references/templates/`.

## The gate hook

`hooks/tenx_gate.py` (via `hooks/tenx-gate.sh`) is a `PreToolUse` hook. It deterministically
blocks:

- reading `skills/{investigate,slice,implement}/SKILL.md` without the full prefix chain of valid
  records for the active issue;
- `gh pr create` / `glab mr create` in a TenX-managed repo without that chain.

The whole chain must be satisfied by one `.tenx/<issue-id>/` directory. Approvals never combine
across issues. The hook fails closed: if `python3` is missing or the verifier cannot run, the
call is denied. A denial is an instruction to run the owning phase, never to write the missing
file yourself.

## Standalone skills

These work independently of the phase chain:

- `tenx:commit-changes` — conventional-commit messages for the working tree.
- `tenx:ship-changes` — branch, commit, push and open a PR/MR on the project's forge.
- `tenx:pr-review-responder` — fetch PR review comments, fix or explain, reply per thread.
- `tenx:quality-gate` — pre-PR review: mechanical scans plus delegated bucket agents.

## Layout

```
.claude-plugin/   Claude Code plugin + marketplace manifests
.codex-plugin/    Codex plugin manifest
hooks/            phase gate and its tests
references/       controls, definitions, review protocol, record templates
skills/           one directory per skill
```

`references/controls.md` holds the rules every phase applies. `references/definitions.md` and
`references/review-protocol.md` are loaded on demand, not upfront.

## Tests

```bash
python3 hooks/test_tenx_gate.py
```

```bash
python3 skills/quality-gate/scripts/test_quality_scan.py && python3 skills/quality-gate/scripts/test_enumerations.py
```

The quality-gate scripts require Python 3.9 or newer.
