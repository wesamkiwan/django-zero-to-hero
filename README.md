# Django Zero to Hero

A complete, hands-on learning path that takes you from **knowing nothing about web
development** to being a **job-ready Django software engineer** — built and version
controlled in the open, one module at a time.

This is not just theory. Every module ships with:
1. A **lesson** written in plain language, assuming no prior web dev knowledge.
2. **Working examples** you run yourself.
3. A **cheat sheet** you can use as a quick reference for the rest of your career.
4. A slice of a real, portfolio-worthy application — **Atlas**.

## What is Atlas?

**Atlas** is the capstone project we build incrementally, module by module:
a **Store Inventory Management + CRM platform**. It touches nearly every capability
a professional Django job expects: custom auth & roles, a real relational data model,
admin customization, forms and class-based views, a REST API, background tasks (Celery),
file/PDF handling, caching, tests, security hardening, and a Dockerized deployment
with CI/CD. By the end, it's a complete project for your portfolio and your GitHub
profile — not a toy to-do app.

## How this repo is organized

```
django-zero-to-hero/
├── ROADMAP.md              <- full syllabus & progress tracker, start here
├── CONTRIBUTING.md          <- professional git workflow (Module 17)
├── CHEATSHEETS/
│   ├── README.md             <- index of every module's cheat sheet
│   └── OVERALL_CHEATSHEET.md  <- all of them, concatenated
├── .github/
│   ├── workflows/ci.yml      <- CI (Module 16): tests + Docker build on every push
│   └── PULL_REQUEST_TEMPLATE.md
├── modules/
│   └── NN-slug/
│       ├── README.md       <- the lesson for this module
│       ├── cheatsheet.md   <- quick reference for this module
│       └── demo/           <- Modules 01-04 only; later modules teach directly via Atlas
└── project/
    └── atlas/               <- the real capstone app, evolves from Module 03 onward
```

## How to use this repo

1. Read `ROADMAP.md` for the full syllabus and to track progress.
2. Go module by module, in order — each one assumes everything before it.
3. Inside each module: read the `README.md`, actually type out and run the examples
   in `demo/` (typing beats copy-pasting for retention), then read `cheatsheet.md`.
4. Follow the "Project" section at the end of each module (from Module 03 on) to
   evolve `project/atlas/` — this is the part that becomes your portfolio piece.
5. Each module is committed and pushed as its own point in history, so you can see
   the project grow commit by commit, exactly like a real codebase evolves.

## Prerequisites

- Basic Python syntax (variables, functions, loops, basic classes) — that's it.
- A computer with internet access. Everything else (Python, Git, VS Code, Django)
  is installed as part of Module 01.

## Status

**Complete** — all 17 modules built, tested, and documented. See
`ROADMAP.md` for the full syllabus (every box checked) and
`CHEATSHEETS/OVERALL_CHEATSHEET.md` for a one-page reference across the
whole course. `project/atlas/README.md` documents Atlas's final state:
75 automated tests at 94% coverage, a REST API, Celery background
tasks, real-world features (uploads/PDFs/exports/notifications),
security hardening verified by `manage.py check --deploy`, and a
Docker + PostgreSQL + Nginx deployment with CI on every push.
