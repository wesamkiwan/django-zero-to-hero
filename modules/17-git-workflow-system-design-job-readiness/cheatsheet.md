# Cheat Sheet — Module 17: Git Workflow, System Design & Job Readiness

## Git workflow (full version: repo-root `CONTRIBUTING.md`)

- **Trunk-based**: short-lived branches (`feat/...`, `fix/...`), merge
  back within days, `main` always deployable.
- **Conventional Commits**: `<type>(<scope>): <imperative summary>` +
  body explaining WHY. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
- **Every change via PR**, even solo/two-person teams — CI must run,
  one other human must look at the diff, no self-merging without review.
- **Reviewer checks**: matches the PR description? tests exist and would
  actually fail without the fix? touches permissions/input/secrets
  (Module 15 checklist)? simplest version of the fix?

## Architecture trade-offs — the pattern to reuse

For every "why did you choose X" question: name the alternative, name
the trade-off, name the CONCRETE trigger that would flip the decision.
"At scale" alone is not an answer.

| Choice made | Alternative | Real trigger to switch |
|---|---|---|
| SQLite (dev) | PostgreSQL (prod) | Concurrent writes (SQLite locks the whole file) |
| LocMemCache | Redis | >1 worker process (each has its own separate cache) |
| Celery | Inline processing | Work whose latency/failure shouldn't block the request |
| Local disk uploads | S3-compatible storage | >1 container replica (disk isn't shared or persistent) |
| Token auth | JWT | Need stateless verification badly enough to accept harder revocation |
| Group permissions | Object-level (django-guardian) | Need to scope access below "everyone in this group" |
| Monolith | Microservices | ONE part needs a genuinely different scaling shape than the rest |
| REST | GraphQL | Multiple clients each needing meaningfully different data shapes |

## Interview questions grounded in Atlas — the shape of a good answer

- **"Walk me through X flow"** → name the actual code path, not a
  generic description (signals, transaction boundaries, what's deferred
  and why).
- **"A bug you fixed"** → a specific failure, a specific root cause, a
  specific test proving the fix — not "I debugged some stuff."
- **"How would you scale this?"** → identify the actual bottleneck
  first; don't reach for "microservices" as a reflex.
- **"How do you know it works?"** → point at the test suite, CI, and any
  specific proof-style test (query counts, timing, deploy checks) — not
  "I tested it manually."
- **"What's not done / what would you change?"** → name something real.
  Honesty about known gaps reads as MORE senior, not less.

## Portfolio presentation

- Resume bullet: outcome + mechanism, not a tool list.
- README = the pitch: name specific mechanisms an interviewer can ask
  follow-up questions about.
- Point at commit history (`git log --oneline`) as evidence of
  incremental, deliberate engineering.
- Have one specific hard problem ready to explain well, end to end.
