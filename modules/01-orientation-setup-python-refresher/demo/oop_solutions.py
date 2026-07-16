"""
Reference solutions for oop_practice.py — only check this AFTER you've tried
each exercise yourself. Run with: python oop_solutions.py
"""


class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price


def check_exercise_1():
    p = Product("Keyboard", 49.99)
    assert p.name == "Keyboard"
    assert p.price == 49.99
    print("Exercise 1: PASS")


class Product2:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    def total_value(self):
        return self.price * self.quantity


def check_exercise_2():
    p = Product2("Mouse", 20.0, 3)
    assert p.total_value() == 60.0
    print("Exercise 2: PASS")


class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name} makes a sound."


class Dog(Animal):
    def speak(self):
        return f"{self.name} barks."


class Cat(Animal):
    def speak(self):
        return super().speak() + " ...and meows."


def check_exercise_3():
    assert Dog("Rex").speak() == "Rex barks."
    assert Cat("Tom").speak() == "Tom makes a sound. ...and meows."
    print("Exercise 3: PASS")


class Counter:
    total_created = 0

    def __init__(self):
        Counter.total_created += 1

    @classmethod
    def how_many(cls):
        return cls.total_created


def check_exercise_4():
    Counter()
    Counter()
    Counter()
    assert Counter.how_many() == 3
    print("Exercise 4: PASS")


def summarize(*args, **kwargs):
    return {"positional": args, "keyword": kwargs}


def check_exercise_5():
    result = summarize(1, 2, name="Atlas", role="CRM")
    assert result == {"positional": (1, 2), "keyword": {"name": "Atlas", "role": "CRM"}}
    print("Exercise 5: PASS")


def check_exercise_6():
    prices = [10, 25, 5, 40, 15]
    expensive = [p for p in prices if p > 15]
    assert expensive == [25, 40]
    doubled = {p: p * 2 for p in prices}
    assert doubled == {10: 20, 25: 50, 5: 10, 40: 80, 15: 30}
    print("Exercise 6: PASS")


class Timer:
    def __enter__(self):
        self.events = []
        self.events.append("started")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.events.append("finished")
        return False


def check_exercise_7():
    with Timer() as t:
        t.events.append("working")
    assert t.events == ["started", "working", "finished"]
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
