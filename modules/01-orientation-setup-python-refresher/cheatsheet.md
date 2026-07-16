# Cheat Sheet — Module 01: Orientation, Environment, Python Refresher

## Core concepts

| Term | Meaning |
|---|---|
| Client | The browser/app that sends requests |
| Server | The program (Django) that responds to requests |
| Frontend | What the user sees (HTML/CSS/JS) |
| Backend | Server-side logic (Django's job) |
| MVT | Model (data) → View (logic) → Template (presentation) |
| Request/Response cycle | Browser asks → server answers, repeat |

## Virtual environments

```bash
python -m venv venv                     # create
venv\Scripts\Activate.ps1               # activate (Windows PowerShell)
source venv/bin/activate                # activate (macOS/Linux)
deactivate                              # exit the venv
```
Never commit `venv/`. Commit `requirements.txt` instead.

## pip

```bash
pip install <package>
pip install <package>==<version>        # pin exact version (recommended)
pip install -r requirements.txt         # install everything listed
pip freeze > requirements.txt           # capture current environment
pip list
pip uninstall <package>
```

## Git essentials

```bash
git status
git add <file>            # or: git add .
git commit -m "message"
git log --oneline
git push
git pull
```

## Django project anatomy (from the hello_django demo)

```
manage.py            # CLI entry point: runserver, migrate, startapp, test, ...
mysite/               # the PROJECT: global settings + root URL config
  settings.py
  urls.py
greetings/            # an APP: one self-contained feature area
  views.py            # functions/classes: request in, response out
  models.py           # data definitions (Module 04)
  admin.py            # admin registration (Module 05)
```

```bash
django-admin startproject <name> .      # create a project in the current dir
python manage.py startapp <name>        # create a new app
python manage.py runserver              # run the dev server (default: :8000)
```

## Python OOP quick reference (Django-relevant)

```python
# Class + constructor
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

# Inheritance + overriding + super()
class Base:
    def greet(self):
        return "hi"

class Child(Base):
    def greet(self):
        return super().greet() + " there"

# Class attribute + classmethod
class Counter:
    total = 0
    def __init__(self):
        Counter.total += 1
    @classmethod
    def how_many(cls):
        return cls.total

# *args / **kwargs — every Django view can receive these
def view(request, *args, **kwargs):
    ...

# Comprehensions
squares = [n * n for n in range(5)]
lookup = {n: n * n for n in range(5)}

# Context manager
with open("file.txt") as f:
    data = f.read()
```

## Mental model to keep forever

```
Request → urls.py (routing) → views.py (logic) → models.py (data)
                                    │
                                    ▼
                          templates/*.html (HTML out)
```
