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
├── CHEATSHEETS/            <- overall cheat sheet (built once all modules are done)
├── modules/
│   └── NN-slug/
│       ├── README.md       <- the lesson for this module
│       ├── cheatsheet.md   <- quick reference for this module
│       └── demo/           <- small throwaway examples for this module's concepts
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

Currently on **Module 01 — Orientation, Environment Setup & Python-for-Django Refresher**.
See `ROADMAP.md` for full progress.
