from django.http import HttpResponse


def home(request):
    """A view is just a Python function: it takes a request, returns a response."""
    return HttpResponse(
        "<h1>It works! Django is running.</h1>"
        "<p>Try visiting <a href='/hello/YourName/'>/hello/YourName/</a></p>"
    )


def hello_name(request, name):
    """URL parameters (here, <str:name>) are passed in as function arguments."""
    return HttpResponse(f"<h1>Hello, {name}!</h1>")
