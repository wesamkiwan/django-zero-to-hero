# Module 01 — Orientation, Environment Setup & Python-for-Django Refresher

> **Where we're going:** by the end of this module you'll understand what a web
> application actually is, why Django exists, have a real professional
> development environment set up, and have refreshed exactly the Python OOP
> concepts you'll lean on for the rest of this course.

## 1. What is software engineering, really?

"Coding" is writing instructions a computer follows. **Software engineering**
is the discipline around that: making code that other people (including future
you) can read, change safely, test, and run reliably in production, under
real constraints (deadlines, changing requirements, a team, users who will
absolutely do things you didn't expect).

The practical differences you'll feel immediately as we build Atlas:
- We use **version control** (Git) from line one, not "when the project is done."
- We write code assuming **someone else will read it** — clear names, small
  functions, no cleverness for its own sake.
- We treat **tests** as part of the feature, not an afterthought (Module 11).
- We separate **configuration from code** (Module 15/16) so the same code runs
  in development, staging, and production.

You'll see all of this in action, not just hear about it.

## 2. What is a web application?

A **web application** is a program that runs on a server and is used through a
browser (or an app that talks to the same server over the network).

```
                HTTP request (e.g. "GET /products/42/")
   Browser  ───────────────────────────────────────────▶   Server
  (Client)                                                  (Django)
            ◀───────────────────────────────────────────
                HTTP response (HTML, JSON, ...)
```

- **Client**: the browser (or mobile app) — it *asks* for things.
- **Server**: a program that *listens* for requests and *responds*. This is
  where Django lives.
- **Frontend**: what the user sees/touches (HTML/CSS/JS in the browser).
- **Backend**: the server-side logic — business rules, database access,
  authentication, APIs. Django is a **backend web framework**.
- **Full-stack**: someone comfortable working on both sides. This course
  teaches backend deeply (Django's job) and enough frontend (Module 02, 09)
  to build real, usable pages.

We'll go much deeper into the request/response cycle in Module 02 — for now,
just anchor on: **a web app's job is to receive a request and return a
response**, over and over, for many users at once.

## 3. What is Django, and why does it exist?

Django is a **Python web framework** — a large, batteries-included toolkit
for building backends: routing, database access (ORM), forms, admin
interface, authentication, security defaults, and more, all pre-built so you
focus on your actual business logic instead of re-inventing plumbing.

It's used in production by Instagram, Pinterest, Mozilla, Disqus, Robinhood,
and thousands of companies of every size — it's a genuinely in-demand,
employable skill, not a toy.

### The MVT pattern

Django organizes code using **Model-View-Template (MVT)** — its own take on
the more famous MVC pattern:

| Layer | Responsibility | Django tool |
|---|---|---|
| **Model** | Defines your data & talks to the database | `models.py` (Module 04) |
| **View** | Business logic: receives a request, decides what to do, returns a response | `views.py` (Module 03, 06, 07) |
| **Template** | How data is presented as HTML | `templates/` (Module 03, 09) |

The **URL dispatcher** (`urls.py`) sits in front of all of this: it looks at
the incoming URL and decides *which view* handles it.

```
Request → urls.py (which view?) → views.py (what to do?) → models.py (get/change data)
                                        │
                                        ▼
                              templates/*.html (render response)
```

This is the mental map for basically everything from here on. Every feature
we add to Atlas touches some subset of: a URL, a view, a model, a template.

## 4. Setting up a professional development environment

We're doing this once, properly, so it doesn't get in your way later.

### 4.1 Python

You already have Python installed. Verify it and note the version:

```bash
python --version
```

### 4.2 A code editor: VS Code

Install [VS Code](https://code.visualstudio.com/) if you don't have it, then
install these extensions (search in the Extensions panel):
- **Python** (Microsoft) — syntax highlighting, linting, debugging.
- **Pylance** — usually comes bundled with the Python extension.
- **Django** (by Baptiste Darthenay or similar) — template syntax highlighting.
- **GitLens** — see git history/blame inline. Optional but very useful.

### 4.3 Virtual environments — the single most important habit

**Problem:** different projects need different (and conflicting) versions of
libraries. If you install everything "globally," projects eventually break
each other.

**Solution:** a **virtual environment (venv)** is an isolated Python
installation just for one project. You create one per project, activate it,
and every `pip install` goes only into that project's environment.

```bash
# Create a venv (do this once, inside your project folder)
python -m venv venv

# Activate it (do this every time you start working)
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows cmd.exe:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# You'll see (venv) appear at the start of your terminal prompt when it's active.

# Deactivate when you're done:
deactivate
```

**Never commit a `venv/` folder to git** — it's machine-specific and can be
huge. Instead, you commit a `requirements.txt` listing what to install, and
anyone (including you, on a new machine) recreates the environment with:

```bash
pip install -r requirements.txt
```

To create that file from your active venv:

```bash
pip freeze > requirements.txt
```

### 4.4 pip — Python's package manager

```bash
pip install django          # install a package into the active venv
pip install django==5.0.6   # install an exact version (recommended for real projects)
pip list                    # see what's installed
pip uninstall django        # remove a package
```

### 4.5 Git — version control refresher

You're already tracking this whole course in git. The commands you'll use
constantly:

```bash
git status                  # what changed since the last commit?
git add <file>               # stage a specific file
git add .                    # stage everything changed (use with git status first!)
git commit -m "message"      # save a snapshot with a description
git log --oneline            # see history
git push                     # send commits to GitHub
git pull                     # fetch + merge remote changes
```

We'll cover branching, pull requests, and team workflow properly in Module 17
— for now, one commit per module is enough to build the habit of *committing
working, described increments* rather than one giant blob at the end.

### 4.6 Hands-on: prove it all works

Go to `demo/hello_django/` in this module and follow its `README.md`. You'll
create a venv, install Django, and run a real (tiny) Django project — the
"it works" moment. Do this now before continuing — the rest of the course
assumes you've felt this loop once already.

## 5. Python OOP refresher — exactly what Django leans on

You said you know Python basics. Django is **deeply object-oriented**: models
are classes, forms are classes, class-based views are classes, and you
constantly subclass things Django provides and override a method or two.
If OOP feels shaky, everything downstream will feel harder than it needs to.

Go to `demo/oop_practice.py` now and work through it — each exercise maps
directly to something you'll type constantly starting Module 03:

1. **Classes & `__init__`** → every Django `Model` you define.
2. **Instance methods** → `product.get_absolute_url()`-style helpers.
3. **Inheritance & overriding, `super()`** → `class ProductListView(ListView):`
   is inheritance; overriding `get_queryset()` and calling `super()` is exactly
   Exercise 3.
4. **Class attributes & `@classmethod`** → model `Meta` options and custom
   manager methods.
5. **`*args, **kwargs`** → nearly every Django view signature:
   `def my_view(request, *args, **kwargs):`.
6. **List/dict comprehensions** → shaping querysets for templates and APIs.
7. **Context managers (`with`)** → `with transaction.atomic():` for database
   transactions (Module 12).

Don't peek at `oop_solutions.py` until you've genuinely attempted each one.

## 6. Checkpoint — you should now be able to:

- [ ] Explain, in your own words, what happens between clicking a link and
      seeing a page appear (client → request → server → response).
- [ ] Explain what MVT stands for and what each piece is responsible for.
- [ ] Create and activate a virtual environment from scratch.
- [ ] Install a package with `pip` and freeze it into `requirements.txt`.
- [ ] Run `git status`, `git add`, `git commit`, `git push` without looking
      them up.
- [ ] Write a Python class with inheritance, override a method, and call
      `super()` correctly.
- [ ] Explain `*args` and `**kwargs` and use them in a function signature.

If any of those feel shaky, redo the relevant section before moving on —
Module 02 builds directly on top of this.

## 7. What's next

**Module 02 — Web & HTTP Fundamentals + HTML/CSS Basics** goes one level
deeper into the request/response cycle (HTTP methods, status codes, cookies,
sessions) and gives you enough HTML/CSS to build real pages, so that when
Module 03 starts writing Django views and templates, none of the surrounding
web concepts are new — only Django's specific way of doing them.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 02.
