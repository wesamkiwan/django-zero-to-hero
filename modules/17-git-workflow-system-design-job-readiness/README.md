# Module 17 — Git/Team Workflow, System Design & Job Readiness (Capstone)

> **Where we're going:** no new Django. This module is the pull-back-and-
> look-at-the-whole-thing module — a professional git workflow (written
> down in `CONTRIBUTING.md`, at the repo root, not buried in a module
> folder), a critical retrospective on the real architecture trade-offs
> made across all 16 prior modules, interview preparation grounded in
> *this specific codebase* rather than generic advice, and how to present
> Atlas as a portfolio piece to someone deciding whether to interview you.

## 1. Professional git workflow

Written up in full at the repo root: **`CONTRIBUTING.md`**. The short
version: this course's own history (`git log --oneline` — seventeen
commits, one per module, straight to `main`) is exactly right for a solo
learner working through a syllabus and exactly wrong for a team. Read
`CONTRIBUTING.md` for the real version — trunk-based short-lived
branches, Conventional Commits, mandatory PR review even on a two-person
team, and what a reviewer is actually checking for.

The one habit worth carrying over regardless of team size: every commit
message in this repo explains **why**, not just what changed — read
`git log -p` on any commit and the body is doing real work, not
restating the diff. That habit outlasts any specific branching strategy.

## 2. Architecture trade-offs — a retrospective, not a tour

Every module made a real choice, in a real direction. Here's each one,
named honestly, with what would actually force it to change:

**SQLite (dev/test) → PostgreSQL (production), Module 16.** SQLite's
whole-database-file locking makes concurrent writes serialize — fine for
one developer's laptop or a single-worker test suite, wrong the moment
two web processes try to write at once. The switch was one `if` block,
not a rewrite, specifically *because* Module 04 never leaned on a
SQLite-only feature.

**LocMemCache (Module 12) → Redis, planned for Module 16's production
config.** `LocMemCache` lives inside one process; a real deployment runs
several Gunicorn workers (Module 16's `--workers 3`), **each with its own
separate cache** — one worker invalidating `low_stock_count` wouldn't
affect the other two, so they'd serve stale data indefinitely. This is
the one piece of the "swap without changing calling code" story that
this course describes but doesn't actually flip in `settings.py` — a
real next step, not yet done here.

**Celery for async work (Module 13), not inline processing.** The
trigger for "this needs a queue" wasn't email specifically — it's *any*
work whose latency shouldn't block a request/response cycle, and whose
failure shouldn't fail the request that triggered it. The trade-off:
operational complexity (a broker, a worker process, monitoring whether
the queue is backing up) in exchange for that decoupling. A low-traffic
internal tool sending three emails a day doesn't need this; Atlas added
it specifically because "the customer's response shouldn't wait on SMTP"
is a real, testable claim (Module 13's tests prove the on_commit()
timing, not just that email eventually sends).

**Local disk → S3-compatible object storage for uploads (Module 16).** Not
a performance choice — a **correctness** one. A container's disk is
ephemeral and not shared between replicas; two Gunicorn containers behind
Nginx would each have their *own* `media/` folder, so an image uploaded
via one wouldn't exist when a different container served the detail
page. This bites teams at the exact moment they scale `web` past one
replica — often well after the original developer left.

**Token authentication (Module 10), not JWT.** DRF's `TokenAuthentication`
is one static, database-backed token per user — trivially revocable
(delete the row) and simple to reason about, but it doesn't carry an
expiry or claims, and checking it is a database hit on every request
(no caching added here). JWTs solve "stateless, self-contained, no DB
hit to verify" at the cost of **not** being trivially revocable — a
stolen JWT is valid until it expires, full stop. Atlas's scale (an
internal-ish CRM/inventory tool, not a public API serving millions of
mobile clients) never needed JWT's stateless-verification win badly
enough to accept its revocation downside.

**Django's Group/Permission model (Module 08), not per-object
permissions.** "Sales Team" is one group with the same Product
permissions for every member — nobody can be scoped to "only the
Electronics category" or "only orders from customers in Texas." That's
fine at Atlas's actual scale (a handful of sales reps, no regulatory
need for row-level isolation) and would become a real limitation the
moment the business needed it — `django-guardian` (object-level
permissions) or a custom scoping layer would be the next step, not a
rewrite of Module 08's foundation.

**A monolith, not microservices.** Every app (`catalog`, `orders`,
`customers`, `accounts`, `notifications`) shares one codebase, one
database, one deploy. This is the *correct* choice for a team this size
building a product at this stage — a monolith is dramatically cheaper to
develop, test (one `pytest` run, Module 11), and deploy (one
`docker-compose up`, Module 16) than a distributed system, and "we might
need to scale a service independently one day" is not, by itself, a
reason to pay that tax today. The concrete trigger that WOULD justify
splitting something out: one part of the system needs a genuinely
different scaling shape than the rest (e.g., product search moving to a
dedicated Elasticsearch-backed service once the catalog is too large for
Postgres full-text search to stay fast) — split that one thing, not
everything, and not preemptively.

**REST (Module 10), not GraphQL.** DRF's per-resource endpoints
over-fetch or under-fetch compared to GraphQL's client-specified queries
— the order list endpoint always returns every field `OrderSerializer`
defines, whether a given screen needs all of them or not. Atlas doesn't
have enough *distinct client shapes* (one web frontend, one API) for
that flexibility to earn its complexity yet; GraphQL earns its keep once
several different frontends (web, mobile, third-party integrators) each
want meaningfully different slices of the same data.

## 3. Interview prep, grounded in this codebase

Generic interview advice is easy to find; being able to talk through a
**real, working system you built** is not. Practice answering these
about Atlas specifically — every one has a concrete, non-generic answer
available in this repo:

**"Walk me through what happens when someone places an order."**
`OrderSerializer.create()` (Module 10) wraps Order + OrderItem creation
in `transaction.atomic()` (Module 13) → `post_save` fires twice (Module
14) → one receiver defers `send_order_confirmation_email.delay()` via
`transaction.on_commit()` so it only queues once the whole order
(including items) has actually committed → the other creates
`Notification` rows for managers, directly, no Celery, because it's a
fast local write with nothing to defer. Two receivers, two different
timing strategies, for two different reasons — that contrast IS the answer.

**"Tell me about a bug you found and fixed."** Three real ones, not
hypotheticals: the `$0.00`-total race (Module 13, signal fired before
`OrderItem`s existed), the Celery `task_always_eager` env-var timing bug
(Module 13, pytest-django's own `django.setup()` runs before your
`conftest.py` does), and the DRF throttle class-attribute caching bug
(Module 15, a setting read once at import time doesn't see a later
override). All three are the *same underlying lesson* wearing different
clothes — "something reads configuration once, early, and caches it" —
which is a much stronger interview answer than three unrelated anecdotes.

**"How would you scale this?"** Don't reach for "microservices" as a
reflex. Walk the actual bottleneck: read-heavy traffic → Redis caching
(already wired, Module 12) and read replicas; write-heavy → look at
which writes are on the hot path and whether they can move to Celery
(Module 13); a specific subsystem outgrowing the rest (search, §2) →
split *that*, with a concrete trigger, not "at scale" as a vague gesture.

**"How do you know your code works?"** Not "I tested it manually" — 75
automated tests (Module 11), `django_assert_num_queries` proving query
counts instead of asserting they "feel" fast (Module 12),
`django_capture_on_commit_callbacks` proving deferred-task timing
(Module 13), and CI running the full suite against the same database
engine production uses (Module 16), on every push.

**"What would you do differently / what's not done?"** Real, honest
answers: `LocMemCache` should be Redis in the actual deployed config
(§2), object-level permissions would matter at more scale (§2), and the
Docker stack (Module 16) was written but not run end-to-end in the
environment that built it — naming that limitation clearly is a better
answer than pretending everything here is flawless.

## 4. Presenting Atlas as a portfolio piece

- **Resume bullet, outcome-first:** "Built and deployed a full-stack
  Django inventory/CRM platform (Atlas) — REST API, async task
  processing with Celery, Dockerized multi-service deployment, 75
  automated tests at 94% coverage — from a from-scratch data model
  through production configuration." Lead with what it does and proves,
  not a tool list.
- **The README is the pitch.** `project/atlas/README.md`'s "Current
  state" section is written to be read by someone deciding whether to
  interview you — it names specific mechanisms (`transaction.on_commit()`,
  `select_related`/`prefetch_related`, `check --deploy`), not just
  buzzwords ("REST API", "caching", "security").
- **Link the commit history, not just the final state.** `git log
  --oneline` shows the project growing module by module — a real
  interviewer skimming that sees deliberate, incremental engineering,
  not one giant "initial commit."
- **Be ready to point at one hard thing and explain it well.** §3's bugs
  are exactly this: a specific, non-trivial thing that went wrong, why,
  and how you knew the fix actually worked (a test, not a guess).

## 5. Checkpoint — you should now be able to:

- [ ] Explain trunk-based development and why long-lived feature
      branches cause pain, and describe what a PR review is actually
      checking for.
- [ ] Name at least four real architecture trade-offs made in Atlas and
      the concrete trigger that would flip each decision.
- [ ] Answer "walk me through placing an order" using the actual two-
      receiver, two-timing-strategy design, not a generic description.
- [ ] Describe the three settings-caching bugs this course hit as one
      underlying lesson, not three disconnected stories.
- [ ] Write your own resume bullet and elevator pitch for Atlas.

## 6. You've finished Django Zero to Hero

Seventeen modules, one continuously evolving application, in Atlas: a
custom data model and admin, full CRUD (function- and class-based), auth
and role-based permissions, a REST API, a real automated test suite,
query optimization and caching, background/scheduled tasks, real-world
features (uploads, PDFs, exports, notifications), security hardening
verified by a real deploy check, and a Dockerized, CI-tested deployment.
That's not a tutorial project anymore — it's a portfolio piece, built the
way real software actually gets built: incrementally, with tests, with
real bugs found and fixed along the way, not just described.

---
See `cheatsheet.md` for a condensed reference. From here: keep building —
the two things this course deliberately left as exercises (object-level
permissions, splitting out a genuinely independent-scaling piece) are
real, portfolio-worthy next steps, not busywork.
