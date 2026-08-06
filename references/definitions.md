# TenX definitions

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
