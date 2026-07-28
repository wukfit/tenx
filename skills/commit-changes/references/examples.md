# Conventional Commit Examples

## Commit Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes nor adds features |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `chore` | Maintenance (deps, configs, scripts) |
| `style` | Formatting, whitespace, missing semicolons |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `build` | Build system or external dependencies |

## Good Examples

```
feat(auth): add password reset flow

What: Implement password reset via email verification
Why: Users frequently get locked out with no recovery option
How: Email-based token verification with 24h expiry
```

```
fix(api): handle null response from payment provider

What: Add null check before accessing payment status
Why: Intermittent 500 errors when provider returns null
How: Defensive check with fallback to pending status
```

```
refactor(orders): extract validation into separate module

What: Move order validation logic to dedicated validator
Why: Order service has grown to 800+ lines, hard to test
How: Pure functions for each validation rule, composed together
```

```
chore(deps): upgrade Next.js to 14.2

What: Bump Next.js from 14.0 to 14.2
Why: Security patch for middleware vulnerability
How: Standard upgrade, no breaking changes in this minor
```

## Bad Examples (and why)

```
fix bug
```
→ No type, no scope, no context. What bug? Where?

```
Fixed the thing that was broken in the user authentication system
```
→ Past tense, vague, too long for subject

```
feat: add button and fix header and update styles
```
→ Multiple unrelated changes — should be separate commits

```
WIP
```
→ Never commit work-in-progress without context

## Scope Conventions

Choose scopes based on your project structure. Common patterns:

- **By feature**: `auth`, `orders`, `payments`, `users`
- **By layer**: `api`, `ui`, `db`, `config`
- **By component**: `button`, `modal`, `sidebar`

Keep scopes consistent within a project. If `authentication` was used before, don't switch to `auth`.