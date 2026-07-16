# Demo: hello_django

A throwaway project used only to prove your environment works and to see a
Django project's real folder structure for the first time. This is **not**
the Atlas capstone project — that starts fresh in Module 03.

## Run it yourself

```bash
# from inside modules/01-orientation-setup-python-refresher/demo/hello_django/
python -m venv venv

# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py runserver
```

Then open:
- http://127.0.0.1:8000/ — a plain "it works" page
- http://127.0.0.1:8000/hello/YourName/ — proves URL parameters reach your view
- http://127.0.0.1:8000/admin/ — Django's built-in admin login page (nothing set
  up yet, but notice it's already fully functional — no code written for it)

Stop the server with `Ctrl+C`. Delete `venv/`, `db.sqlite3`, and `__pycache__/`
folders if you want to reset — none of those are (or should be) committed to git.

## What to notice

- `manage.py` — the command-line entry point for every Django task (`runserver`,
  `migrate`, `startapp`, `test`, ...).
- `mysite/` — the **project**: global settings, root URL configuration.
- `greetings/` — an **app**: a self-contained unit of functionality. A project
  is made of one or more apps.
- `greetings/views.py` — a view is just a Python function (or class, later)
  that takes a request and returns a response.
- `mysite/urls.py` — maps URL paths to views.

This project/app split is central to how Django is organized — see the main
`README.md` in this module for the full explanation.
