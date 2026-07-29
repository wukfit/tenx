---
name: pr-review-responder
description: Review and respond to GitHub PR review comments. Use when asked to address PR feedback, resolve review comments, or respond to code review. Fetches comments, plans resolutions, makes code changes where needed, and replies to each comment thread individually with either the fixing commit or an explanation.
---

# PR Review Responder

The commands below are written for GitHub (`gh`). On another forge, keep the workflow, categories and verification rules identical and map each API call to the forge's equivalent (GitLab: merge-request discussions via `glab api`; unrecognized forge: ask the user). The thread rule is universal: always reply in the specific review thread, never the main PR/MR conversation.

## Workflow

### 1. Fetch Review Comments

```bash
# Get the current PR number if in a feature branch
gh pr view --json number,url,headRefName

# Fetch all review comments (not issue comments)
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --paginate
```

Review comments have `path`, `line`, `body`, and `id` fields. Group by `in_reply_to_id` to identify threads.

### 2. Analyze and Plan

For each top-level comment thread, categorize:

| Category | Action |
|----------|--------|
| **Valid fix needed** | Plan code change, note which files/lines |
| **Already addressed** | Note the existing code that resolves it |
| **Disagree/Won't fix** | Prepare clear technical rationale |
| **Scope creep** | Push back — suggestion beyond PR scope or improves code slated for deletion |
| **Clarification needed** | Ask specific follow-up question |
| **Nitpick/Style** | Fix if trivial, otherwise explain tradeoff |

**Verification rule — accepting comments (CRITICAL):** Before implementing a reviewer's suggestion, verify any factual claims they make against the actual codebase — be rigorous in this task. Reviewers (human or automated) may assert things about code behaviour, usage patterns, existing conventions, or system state that are incorrect or outdated. Search the code to confirm before acting.

Example: A reviewer says "narrow this to 401 only because 403 is too broad." Before implementing, check how many API routes actually return 401 vs 403 for authentication failures. If 44 of 47 routes return 403, the suggestion would break the feature — push back with evidence.

Proceed autonomously after verification. Present the plan to the user or main thread only when comments reveal a substantive critical issue that signals something went wrong earlier and the caller must decide whether to stop or re-scope implementation. Examples include a security regression, invalid core design, contradictory requirement, or major unexpected scope expansion. Routine valid fixes, nits, already-addressed comments, and evidence-backed pushback do not require approval.

### 3. Make Code Changes

For comments requiring fixes:
- Make the change
- Commit with a descriptive message referencing the feedback
- Use atomic commits (one logical change per commit)

### 4. Reply to Each Comment Thread

**Critical: Always reply to the specific comment thread, never the main PR conversation.**

```bash
# Reply to a review comment thread (use in_reply_to parameter)
gh api -X POST repos/{owner}/{repo}/pulls/{pr_number}/comments \
  -f body="<response>" \
  -F in_reply_to={comment_id}
```

Use the `id` of the top-level comment in the thread (the one without `in_reply_to_id`, or the root).

**Note:** The `/replies` sub-resource endpoint (`/comments/{id}/replies`) returns 404 — use the main `/comments` endpoint with `in_reply_to` parameter instead.

#### If the Reply API Fails

**DO NOT fall back to main PR comments or `gh pr review --comment`.** Instead:

1. Check the error message (permissions? wrong endpoint? bot comment restrictions?)
2. **Ask the user for help** — do not work around by commenting on main thread
3. Document what you tried so the user can debug

#### Response Templates

**Fixed with commit:**
```
Fixed in <commit_sha_short> — <brief description of change>
```

**Won't change (with rationale):**
```
Keeping as-is: <technical reason>. <optional: tradeoff explanation or link to docs>
```

**MVP scope (defer to future):**
```
Noted for future. <reason why acceptable now>. Current scale: <metric>.
```

**Already addressed (in batch commit):**
```
Addressed in <commit_sha_short> with <pattern/approach>.
```

**Acceptable tradeoff:**
```
Acknowledged. <why the tradeoff is acceptable for this context>.
```

**Scope creep (feature flag rollout):**
```
Legacy path will be removed after feature flag validation — deferring optimization.
```

**Scope creep (out of diff):**
```
Out of scope for this PR. <optional: created issue #X to track>.
```

**Clarification:**
```
Could you clarify <specific question>? I interpreted this as <your understanding>.
```

#### MVP Context

Many review comments suggest production-grade patterns that add complexity without proportional value for MVP:

| Pattern | When to Defer |
|---------|---------------|
| Pagination | <100 items expected, admin-only endpoint |
| Saga/compensation | Cleanup complexity > partial failure cost |
| Extensive JSDoc | Self-documenting code, internal functions |
| Retry/circuit breaker | Manual retry acceptable, not critical path |
| Full error wrapping | Clear context already in error message |

When deferring, acknowledge the concern and state the threshold that would trigger implementation.

### 5. Resolve Comment Threads

After replying to all comments, resolve the threads:

```bash
# Get all review thread IDs
gh api graphql -f query='
query {
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr_number}) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
        }
      }
    }
  }
}'

# Resolve each unresolved thread
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "{thread_id}"}) { thread { isResolved } } }'
```

For many threads, batch the resolution calls to avoid rate limits (add `sleep 0.2` between calls).

### 6. Push and Summarize

```bash
git push
```

Provide a summary: how many comments addressed, commits made, any needing further discussion.