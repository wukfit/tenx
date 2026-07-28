---
name: ship-changes
description: Ship local changes as a pull/merge request on the project's forge (GitHub, GitLab, etc). Handles branch creation (never commits to the default branch), commits via the commit-changes skill, pushes, and opens the PR/MR. Use whenever the user says "ship", "ship it", "yeet", "ship changes", "send pr", "send a pr", "create pr", "open pr", "open a pull request", or asks to turn local work into a PR.
---

# Ship Changes

End-to-end: local changes → pull/merge request on the project's forge.

## Prerequisites

- `git` plus the forge CLI installed and authenticated (`gh` for GitHub, `glab` for GitLab)
- bundled [commit-changes](../commit-changes/SKILL.md) skill (used for commit messages)

## Workflow

### 0. Detect forge and default branch

```bash
git remote get-url origin
base=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
```

- Remote host contains `github` → forge is GitHub, use `gh`.
- Remote host contains `gitlab` → forge is GitLab, use `glab`.
- Anything else (Bitbucket, Gitea, unrecognized self-hosted) → STOP and ask the user which forge and what PR-creation command to use. Do not guess.
- `$base` is the default branch. Never assume `main`; use `$base` everywhere below.

### 1. Branch check

Run `git branch --show-current`.

- **On `$base`**: do NOT commit here. Create branch from the intended commit subject (kebab-case, ≤50 chars, strip type prefix like `feat:`).
  - First, peek at the diff (`git diff` + `git diff --staged`) to infer the commit subject you'd use.
  - `git checkout -b <kebab-subject>`
- **Not on `$base`**: stay on current branch.

### 2. Logical unit check

Get the list of commits that will be in the PR:

```bash
git fetch origin "$base" --quiet
git log origin/"$base"..HEAD --oneline
```

Plus any uncommitted work (`git status`, `git diff`, `git diff --staged`).

**One logical unit** means all commits address the same problem/feature. Related types combine fine:
- `feat: X` + `test: X` ✅
- `feat: X` + `refactor: X` (same area) ✅
- `feat: X` + `chore: bump dep for X` ✅
- `feat: auth` + `feat: billing` ❌ (split)
- `feat: X` + `refactor: unrelated Y` ❌ (split)

If not one unit, STOP. Tell user which commits belong together, recommend splitting into multiple PRs, and ask how to proceed. Don't guess.

### 3. Commit

If there are uncommitted changes, invoke the bundled [commit-changes](../commit-changes/SKILL.md) skill to create the commit(s). Read it and follow it (resolve the path from this SKILL.md's installed location, not the working directory).

If nothing to commit and no new commits vs `origin/$base`, stop — nothing to ship.

### 4. Push

```bash
branch=$(git branch --show-current)
test "$branch" = "$base" && { echo "refusing to push the default branch"; exit 1; }
git push -u origin "$branch"
```

The default-branch guard is belt-and-braces — step 1 should've already handled it.

### 5. Open PR/MR

Base/target: `$base`. Ready (not draft) unless user said otherwise.

**Title**:
- 1 commit → commit subject
- >1 commit → subject of first `feat:` commit; if none, first `chore:` commit; if neither, ask user

**Body**:
- 1 commit → commit body verbatim
- >1 commit → synthesize:
  - `# Problem` — what the PR addresses (pull from commit bodies)
  - `# Changes` — functional changes only, bulleted. Focus on behavior/capability delivered, not file-by-file diff.

Create via the forge detected in step 0:

```bash
# GitHub
gh pr create --base "$base" --title "<title>" --body "<body>"

# GitLab
glab mr create --target-branch "$base" --title "<title>" --description "<body>"
```

Print the PR/MR URL from the CLI output.

## Notes

- Never force-push.
- Never commit on the default branch, even if user insists — tell them to switch branches.
- If CLI auth fails or remote missing, surface the error; don't try to fix silently.
- Branch name derivation: lowercase, spaces→`-`, strip punctuation, drop conventional-commit prefix. E.g. `feat: add patient self-booking` → `add-patient-self-booking`.
