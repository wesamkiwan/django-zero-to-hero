# Roadmap — Django Zero to Hero

This is the full syllabus. Each module lives in `modules/NN-slug/` and contains:
- `README.md` — the lesson (explanations, examples, hands-on steps)
- `cheatsheet.md` — a quick-reference summary of that module
- `demo/` — small throwaway example projects/scripts used to practice the concept in isolation

Alongside the modules, we build one continuous portfolio project — **Atlas**, a
Store Inventory Management + CRM platform — inside `project/atlas/`, starting in Module 3.
Every module from Module 3 onward adds a real slice of Atlas, so by the end you have a
complete, deployed, tested, documented application for your portfolio.

Check items off as you complete them. Progress is tracked here and in commit history.

## Modules

- [x] **01 — Orientation, Environment Setup & Python-for-Django Refresher**
      What software/web engineering actually is, how the web works at a high level,
      professional dev environment (Python, venv, VS Code, Git), and the OOP concepts
      Django leans on constantly.
- [x] **02 — Web & HTTP Fundamentals + HTML/CSS Basics**
      The request/response cycle, HTTP methods & status codes, cookies/sessions,
      enough HTML/CSS to build real pages.
- [x] **03 — Django Fundamentals: Projects, Apps, URLs, Views, Templates**
      Django's architecture (MVT), starting the Atlas project, first app, first views,
      first templates, static files.
- [x] **04 — Models & the ORM**
      Defining models, migrations, relationships (FK/M2M/O2O), QuerySets, managers.
      Atlas gets its real data model: products, categories, customers, suppliers, orders.
- [x] **05 — Django Admin Mastery**
      Customizing ModelAdmin, inlines, list filters/search, actions, admin permissions.
- [x] **06 — Forms & Function-Based Views (CRUD)**
      Forms, ModelForms, validation, CSRF, building full CRUD by hand.
- [x] **07 — Class-Based Views & Generic Views**
      ListView/DetailView/CreateView/UpdateView/DeleteView, mixins, when to use CBVs vs FBVs.
- [x] **08 — Authentication, Authorization & Permissions**
      Login/logout/signup, custom User model, groups & permissions, role-based access
      (staff / manager / sales rep / customer) for Atlas.
- [x] **09 — Templates & Frontend Polish**
      Template inheritance, custom template tags/filters, Bootstrap integration, dashboards.
- [ ] **10 — Django REST Framework: Building APIs**
      Serializers, viewsets, routers, authentication (token/JWT), permissions, pagination.
      Atlas gets a full REST API.
- [ ] **11 — Testing**
      pytest-django, the Django test client, factories, coverage, a TDD mindset.
- [ ] **12 — Advanced ORM, Query Optimization & Caching**
      select_related/prefetch_related, aggregation/annotation, N+1 queries, indexes, Redis caching.
- [ ] **13 — Celery & Background/Async Tasks**
      Long-running work off the request/response cycle, scheduled jobs, async emails.
- [ ] **14 — Real-World Features**
      File/image uploads, PDF invoice generation, CSV/Excel export, search & filtering, notifications.
- [ ] **15 — Security Best Practices**
      OWASP Top 10 in a Django context, settings hardening, secrets management.
- [ ] **16 — Configuration, Docker & Deployment**
      Environment-based settings, Docker & docker-compose, PostgreSQL, Gunicorn/Nginx,
      CI/CD with GitHub Actions, deploying Atlas live.
- [ ] **17 — Git/Team Workflow, System Design & Job Readiness (Capstone)**
      Professional Git workflow, architecture trade-offs at scale, interview prep,
      presenting Atlas as a portfolio piece.

## Overall cheat sheet

Once all modules are complete, `CHEATSHEETS/OVERALL_CHEATSHEET.md` aggregates every
module's cheat sheet into one single reference document.
