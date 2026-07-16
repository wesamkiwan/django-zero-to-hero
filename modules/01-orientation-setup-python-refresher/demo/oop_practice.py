"""
Python OOP practice — the exact patterns Django uses constantly.

Do NOT look at oop_solutions.py until you've genuinely tried each TODO.
Run this file with:  python oop_practice.py
It will print PASS/FAIL for each exercise as you fill things in.
"""


# ---------------------------------------------------------------------------
# Exercise 1 — classes, __init__, self
#
# Django models, forms, and views are ALL defined as classes you customize by
# subclassing something Django provides. This is the pattern you'll type
# hundreds of times, so it needs to be second nature.
# ---------------------------------------------------------------------------

class Product:
    # TODO: write __init__(self, name, price) that stores both as attributes
    pass


def check_exercise_1():
    p = Product("Keyboard", 49.99)
    assert p.name == "Keyboard"
    assert p.price == 49.99
    print("Exercise 1: PASS")


# ---------------------------------------------------------------------------
# Exercise 2 — instance methods
#
# Django model instances have methods like product.get_absolute_url().
# ---------------------------------------------------------------------------

class Product2:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    # TODO: write a method total_value(self) that returns price * quantity
    def total_value(self):
        pass


def check_exercise_2():
    p = Product2("Mouse", 20.0, 3)
    assert p.total_value() == 60.0
    print("Exercise 2: PASS")


# ---------------------------------------------------------------------------
# Exercise 3 — inheritance & method overriding
#
# Nearly every Django class you write is "class MyThing(SomeDjangoBase):".
# Understanding override + super() is essential.
# ---------------------------------------------------------------------------

class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name} makes a sound."


class Dog(Animal):
    # TODO: override speak() to return f"{self.name} barks."
    pass


class Cat(Animal):
    # TODO: override speak() but call the parent version too, using super(),
    # and append " ...and meows." to whatever the parent returns.
    pass


def check_exercise_3():
    assert Dog("Rex").speak() == "Rex barks."
    assert Cat("Tom").speak() == "Tom makes a sound. ...and meows."
    print("Exercise 3: PASS")


# ---------------------------------------------------------------------------
# Exercise 4 — class attributes vs instance attributes, classmethods
#
# Django model "Meta" options and manager methods use this pattern.
# ---------------------------------------------------------------------------

class Counter:
    total_created = 0  # class attribute, shared by ALL instances

    def __init__(self):
        # TODO: every time a Counter is created, increment Counter.total_created
        pass

    @classmethod
    def how_many(cls):
        # TODO: return the current total_created count
        pass


def check_exercise_4():
    Counter()
    Counter()
    Counter()
    assert Counter.how_many() == 3
    print("Exercise 4: PASS")


# ---------------------------------------------------------------------------
# Exercise 5 — *args, **kwargs
#
# Django view functions and class methods pass these around constantly,
# e.g. def my_view(request, *args, **kwargs).
# ---------------------------------------------------------------------------

def summarize(*args, **kwargs):
    # TODO: return a dict: {"positional": args, "keyword": kwargs}
    pass


def check_exercise_5():
    result = summarize(1, 2, name="Atlas", role="CRM")
    assert result == {"positional": (1, 2), "keyword": {"name": "Atlas", "role": "CRM"}}
    print("Exercise 5: PASS")


# ---------------------------------------------------------------------------
# Exercise 6 — list & dict comprehensions
#
# You will use these constantly when shaping querysets into template/API data.
# ---------------------------------------------------------------------------

def check_exercise_6():
    prices = [10, 25, 5, 40, 15]

    # TODO: expensive = a list of every price > 15, using a list comprehension
    expensive = []
    assert expensive == [25, 40]

    # TODO: doubled = a dict mapping each price to price * 2, using a dict comprehension
    doubled = {}
    assert doubled == {10: 20, 25: 50, 5: 10, 40: 80, 15: 30}

    print("Exercise 6: PASS")


# ---------------------------------------------------------------------------
# Exercise 7 — context managers (the "with" statement)
#
# Django uses these for transactions: "with transaction.atomic(): ...".
# ---------------------------------------------------------------------------

class Timer:
    """A minimal context manager: __enter__ runs on 'with', __exit__ runs after."""

    def __enter__(self):
        self.events = []
        self.events.append("started")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.events.append("finished")
        return False  # False means: don't suppress exceptions


def check_exercise_7():
    # TODO: use `with Timer() as t:` and inside the block do t.events.append("working")
    # then assert t.events == ["started", "working", "finished"]
    pass
    print("Exercise 7: PASS")


if __name__ == "__main__":
    check_exercise_1()
    check_exercise_2()
    check_exercise_3()
    check_exercise_4()
    check_exercise_5()
    check_exercise_6()
    check_exercise_7()
    print("\nAll exercises passed! You're ready for Module 02.")
