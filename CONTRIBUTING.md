# Contributing / Git Workflow

This file describes the git workflow a **real team** would use on a
project like Atlas. It's written in Module 17 of the course, as a
deliberate contrast: every commit in this repo's own history
(`git log --oneline`) went straight to `main`, one module at a time —
appropriate for a solo learner working through a syllabus, where every
commit already represents one finished, reviewed-by-the-author unit of
work, and there's no second person to review a pull request anyway.
A team, even a team of two, should not work this way. Below is how they should.

## Branching model

**Trunk-based, not long-lived feature branches.** `main` is always
deployable. Work happens on short-lived branches (hours to a few days,
not weeks) that merge back quickly:

```
main
 └── feat/order-refund-flow      (branches off main, merges back within a day or two)
 └── fix/invoice-pdf-total       (same)
```

Long-lived branches (a `develop` branch, per-feature branches that live
for weeks) tend to accumulate painful merge conflicts and let `main`
drift out of sync with what's actually been tested — the opposite of
what CI (Module 16) is for.

## Branch naming

`<type>/<short-description>`, matching the commit type below:
`feat/product-bulk-import`, `fix/order-total-rounding`,
`refactor/catalog-query-helpers`.

## Commit messages — Conventional Commits

```
<type>(<optional scope>): <short summary, imperative mood>

<optional longer body — the WHY, not a restatement of the diff>
```

Types: `feat` (new capability), `fix` (bug fix), `refactor` (no behavior
change), `test`, `docs`, `chore` (deps, config), `perf`.

```
feat(orders): queue confirmation email via transaction.on_commit

Signal fired before OrderItems existed, computing a $0.00 total.
Wrapping serializer.create() in atomic() + deferring to on_commit()
guarantees the whole order (items included) has committed first.
```

This course's own commit messages (`git log`) already follow this shape
loosely — "Module NN: <what>" plus a body explaining *why*, not just what
changed. That "why, not what" habit is the one part of this repo's
commit style worth keeping even in a team setting; the "one commit per
module" granularity is not — a team commits far more often, in much
smaller units.

## Pull requests

Every change to `main` goes through a PR, even a tiny one, even on a
two-person team — not bureaucracy, but the one forcing function that
guarantees: CI ran (Module 16), and at least one other human looked at
the diff before it reached everyone else's `main`. See
`.github/PULL_REQUEST_TEMPLATE.md` for the checklist this repo would use.

**What a reviewer is actually checking:**
- Does this match what the PR description says it does?
- Are there tests for the new behavior — and do they actually fail
  without the fix (this course's own Module 13/15/16 stories are exactly
  the kind of thing a good test catches; a bad test wouldn't)?
- Any security-sensitive code (permissions, user input, secrets) —
  Module 15's checklist applies to every PR, not just once.
- Is this the simplest version of the fix, or did it bring along
  unrelated cleanup that makes the diff harder to review?

**What merges a PR:** CI green + at least one approval. Never merge your
own PR without review just because you're confident — that defeats the
entire point, and it's exactly the moment an overlooked edge case slips
through.

## Code review etiquette

- Review what the PR changes, not everything you notice — file a
  separate issue/PR for unrelated cleanup instead of scope-creeping
  someone else's review.
- Ask questions ("why this approach over X?") before asserting a
  problem exists — you may be missing context the author has.
- Approve with comments for nitpicks that don't need to block merging;
  reserve "request changes" for things that actually must be fixed first.

## Releases

Tag `main` at meaningful points (`v1.0.0`, following semantic
versioning — breaking change = major, new capability = minor, fix =
patch). Module 16's CI pipeline is the natural place to eventually add
"tag on main → auto-deploy," once the team trusts it enough not to want
a manual gate in between.
