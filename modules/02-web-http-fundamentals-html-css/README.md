# Module 02 — Web & HTTP Fundamentals + HTML/CSS Basics

> **Where we're going:** by the end of this module, HTTP methods, status
> codes, headers, cookies, and sessions stop being trivia and become things
> you can predict and reason about. You'll also have enough HTML/CSS to build
> a real page, so Module 03's Django templates only teach you the Django-specific
> parts, not HTML from zero.

## 1. The request/response cycle, one level deeper

Recall from Module 01: browser sends a **request**, server sends a **response**.
Let's open that up.

### Anatomy of a URL

```
https://atlas.example.com:443/products/42/?sort=price#reviews
└─┬──┘   └───────┬────────┘└┬┘└──────┬────┘└────┬────┘└──┬───┘
scheme         host        port     path    query string  fragment
```

- **scheme** — `http` or `https` (`https` = encrypted via TLS).
- **host** — the server's address (domain name, resolved to an IP via DNS).
- **port** — which "door" on that server (`80` default for http, `443` for
  https — usually hidden because they're the defaults).
- **path** — which resource on the server (this is what Django's `urls.py`
  matches against).
- **query string** — `?key=value&key2=value2`, extra parameters (Django:
  `request.GET`).
- **fragment** — `#reviews`, handled entirely by the browser, never sent to
  the server at all.

### HTTP methods — the "verb" of a request

| Method | Meaning | Django usage |
|---|---|---|
| `GET` | "give me this resource" — no side effects expected | Viewing a page, a product list |
| `POST` | "create/submit something" | Submitting a form, placing an order |
| `PUT` | "replace this resource entirely" | Full update via an API (Module 10) |
| `PATCH` | "partially update this resource" | Partial update via an API |
| `DELETE` | "remove this resource" | Deleting via an API |
| `HEAD` | like GET, but headers only, no body | Checking if something changed |
| `OPTIONS` | "what methods does this endpoint support?" | CORS preflight, API discovery |

Rule of thumb you'll enforce constantly in Django: **GET must never change
data**. Browsers, proxies, and crawlers assume GET is "safe" and may repeat
it freely (retries, prefetching, link previews). Anything that changes state
(creating an order, deleting a customer) must be POST/PUT/PATCH/DELETE.

### HTTP status codes — the "verdict" of a response

| Range | Category | Common examples |
|---|---|---|
| 1xx | Informational | rarely seen directly |
| 2xx | Success | `200 OK`, `201 Created`, `204 No Content` |
| 3xx | Redirection | `301 Moved Permanently`, `302 Found`, `304 Not Modified` |
| 4xx | Client error — **you** did something wrong | `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `405 Method Not Allowed` |
| 5xx | Server error — **the server** did something wrong | `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable` |

You'll see these constantly while debugging Django: a `404` means your URL
pattern didn't match anything; a `500` means an unhandled exception happened
inside your view; a `403` usually means a permission or CSRF check failed.
Knowing the category instantly narrows down where to look.

### Headers — metadata riding along with the message

**Request headers** (client → server), the ones you'll actually touch:
- `Host` — which site, when a server hosts multiple domains
- `User-Agent` — identifies the browser/client
- `Content-Type` — format of the request body (e.g. `application/json`,
  `application/x-www-form-urlencoded`, `multipart/form-data` for file uploads)
- `Authorization` — credentials/tokens (Module 10: API auth)
- `Cookie` — sends back any cookies the server previously set

**Response headers** (server → client):
- `Content-Type` — format of the response body (`text/html`, `application/json`)
- `Set-Cookie` — server asking the browser to store a cookie
- `Content-Length`, `Cache-Control`, `Location` (used with redirects)

### Cookies & sessions — faking memory over a memoryless protocol

HTTP is **stateless**: every request is independent: the server doesn't
inherently remember you between requests. But real apps need to know
"you're logged in" across many requests. The trick:

1. You log in. Server creates a **session** (a record, usually in the
   database) and gives it a random ID.
2. Server sends `Set-Cookie: sessionid=<random-id>` in the response.
3. Your browser stores that cookie and **automatically** sends it back
   (`Cookie: sessionid=<random-id>`) on every subsequent request to that site.
4. Server looks up that ID, finds your session data (e.g. "user #7 is logged in").

This is exactly what Django's `django.contrib.sessions` does for you, and
what `request.session` and authenticated `request.user` are built on
(Module 08 covers this in depth).

## 2. See it for real, not just in a diagram

Go to `demo/raw_http/README.md` and follow it. It shows a real, captured
`curl -v` transcript against a real running server, then maps every line
back to the concepts above. Reproduce it yourself — seeing the literal text
that gets sent over the wire makes all of this concrete.

Then open any website in your browser, press **F12** (DevTools), go to the
**Network** tab, reload the page, and click on the first request. You'll see
the same request line, headers, status code, and response headers — just
presented as a UI instead of raw text.

## 3. Enough HTML to build a real page

HTML describes **structure and meaning**, not appearance (that's CSS's job).

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Page title (shown in the browser tab)</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>...</header>
    <nav>...</nav>
    <main>
        <h1>Main heading (one per page)</h1>
        <p>A paragraph.</p>
        <a href="/somewhere/">A link</a>
        <img src="photo.jpg" alt="Description for screen readers">
    </main>
    <footer>...</footer>
</body>
</html>
```

Elements worth knowing well because Django templates and forms revolve
around them:

- **Semantic layout tags**: `<header>`, `<nav>`, `<main>`, `<section>`,
  `<article>`, `<footer>` — describe *what a region is for*, not just
  "a box." Screen readers and search engines use this; so should you.
- **Forms**: `<form method="post" action="...">` wraps `<input>`,
  `<textarea>`, `<select>`, and a submit `<button>`. Every attribute here
  (`method`, `action`, `name`) has a direct Django counterpart — Django's
  `{% csrf_token %}` (Module 06) is injected inside exactly this tag.
- **Tables**: `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` — you'll
  use these for admin-style list views.

## 4. Enough CSS to make it not look like 1995

CSS **selects** elements and applies **rules**.

```css
selector {
    property: value;
}

.some-class { color: #1a1a2e; }     /* class selector: matches class="some-class" */
#some-id    { font-weight: bold; }  /* id selector: matches id="some-id", one per page */
p           { margin: 0; }          /* tag selector: matches every <p> */
```

### The box model (the single most important CSS concept)

Every element is a box: `content` → `padding` (inside the border) →
`border` → `margin` (outside the border, invisible spacing to neighbors).

```css
* { box-sizing: border-box; } /* almost always want this: width/height
                                   include padding+border, no surprise math */
```

### Layout with Flexbox and Grid (the two you actually need)

```css
/* Flexbox: one dimension — a row or a column of items */
.header-row {
    display: flex;
    justify-content: space-between; /* space along the main axis */
    align-items: center;            /* alignment on the cross axis */
}

/* Grid: two dimensions — rows AND columns, e.g. a product card grid */
.product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
}
```

## 5. Hands-on: build/inspect a real static page

Open `demo/static_site/index.html` directly in your browser (double-click
the file, or drag it into a browser tab — no server needed for a static
file). This is a plain HTML/CSS mockup of the **Atlas** storefront — no
Django yet. It exists so that when Module 03 introduces Django templates,
you're learning *how Django injects dynamic data into HTML you already
understand*, not HTML itself.

While it's open:
1. Right-click → **Inspect** to open DevTools on the **Elements** tab —
   hover over lines of HTML and watch the matching box highlight on the page.
2. Try editing a CSS value live in DevTools (e.g. change `.hero`'s
   `background`) and watch it update instantly — nothing is saved, it's a
   scratchpad for experimenting.
3. Resize your browser window narrower — notice the product grid re-flows.
   That's `auto-fit`/`minmax` doing responsive layout without a single
   media query.

## 6. Checkpoint — you should now be able to:

- [ ] Break a URL down into scheme/host/port/path/query/fragment.
- [ ] Explain the difference between GET and POST, and why GET must never
      change data.
- [ ] Say what category (2xx/3xx/4xx/5xx) a status code belongs to just by
      its first digit, and what that category implies about who's at fault.
- [ ] Explain how a session cookie lets a stateless protocol "remember" a
      logged-in user.
- [ ] Write a valid HTML page from scratch with a header, nav, main content,
      and a form.
- [ ] Explain the CSS box model and lay out a row (flexbox) and a grid
      (CSS grid) without looking anything up.

## 7. What's next

**Module 03 — Django Fundamentals** starts the real Atlas project: you'll map
everything from this module (URLs, methods, status codes) directly onto
Django's `urls.py` and `views.py`, and turn the static HTML from this module
into real, dynamic Django templates.

---
Next: see `cheatsheet.md` for a condensed reference, then move to Module 03.
