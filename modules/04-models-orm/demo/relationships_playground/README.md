# Demo: relationships playground (FK, O2O, M2M in isolation)

Atlas's real schema only needed `ForeignKey` and `ManyToManyField` naturally.
This tiny classic Author/Book/Genre project exists purely so you see **all
three** relationship types side by side, including a `OneToOneField`, which
Atlas doesn't happen to need.

`library/models.py`:
- `Author` ←FK— `Book` (many books, one author) — related_name `books`
- `Author` ←O2O— `AuthorProfile` (exactly one profile per author) — related_name `profile`
- `Book` ←M2M— `Genre` (a book can have many genres, a genre many books) — related_name `books`

## Run it yourself

```bash
python -m venv venv
venv\Scripts\Activate.ps1     # or: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py shell
```

Then, in the shell:

```python
from library.models import Author, AuthorProfile, Genre, Book

tolkien = Author.objects.create(name="J.R.R. Tolkien")
AuthorProfile.objects.create(author=tolkien, website="https://example.com/tolkien")

fantasy = Genre.objects.create(name="Fantasy")
classics = Genre.objects.create(name="Classics")

hobbit = Book.objects.create(title="The Hobbit", author=tolkien)
hobbit.genres.add(fantasy, classics)

lotr = Book.objects.create(title="The Lord of the Rings", author=tolkien)
lotr.genres.add(fantasy)
```

## What we verified running exactly that (real output)

```pycon
>>> hobbit.author                      # FK forward
J.R.R. Tolkien
>>> tolkien.books.all()                # FK reverse — related_name="books"
[<Book: The Hobbit>, <Book: The Lord of the Rings>]

>>> tolkien.profile                    # O2O forward — related_name="profile"
Profile of J.R.R. Tolkien
>>> tolkien.profile.author             # O2O reverse
J.R.R. Tolkien

>>> hobbit.genres.all()                # M2M forward
[<Genre: Fantasy>, <Genre: Classics>]
>>> fantasy.books.all()                # M2M reverse — related_name="books"
[<Book: The Hobbit>, <Book: The Lord of the Rings>]

>>> AuthorProfile.objects.create(author=tolkien, website="https://example.com/duplicate")
IntegrityError: UNIQUE constraint failed: library_authorprofile.author_id
```

That last line is the important one: `OneToOneField` is implemented as a
`ForeignKey` with `unique=True` under the hood — the database itself refuses
a second profile for the same author. This is *why* you reach for O2O
instead of FK when the relationship really is "at most one."

## Key takeaways

- **ForeignKey** — "many of these belong to one of those." Always accessible
  forward (`book.author`); accessible in reverse via `related_name`
  (defaults to `<model>_set`, e.g. `author.book_set`, if you don't set one —
  **always set `related_name` explicitly**, it reads far better).
- **OneToOneField** — a FK with a uniqueness constraint added. Use it to
  split a model into "core" and "extra/optional" data, or to extend a model
  you don't own (this is exactly how you'd attach extra fields to Django's
  built-in `User` model before Module 08 introduces swapping it entirely).
- **ManyToManyField** — Django manages a hidden join table for you
  automatically. Only one side needs to declare the field; both sides get a
  manager (`.add()`, `.remove()`, `.set()`, `.all()`).
- Always pass `on_delete` explicitly on every FK/O2O — there's no sane
  default. `CASCADE` (delete children too), `PROTECT` (refuse to delete the
  parent while children exist), and `SET_NULL` (requires `null=True`) cover
  the vast majority of real cases — see which Atlas model uses which and why
  in the main lesson.
