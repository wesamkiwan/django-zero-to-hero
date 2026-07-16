# Cheat Sheet — Module 02: Web & HTTP Fundamentals + HTML/CSS

## URL anatomy

```
https://host:port/path?query#fragment
```
Fragment never reaches the server. Query string → Django's `request.GET`.

## HTTP methods

| Method | Use | Changes data? |
|---|---|---|
| GET | fetch a resource | No — must be safe/idempotent |
| POST | create / submit | Yes |
| PUT | replace entirely | Yes |
| PATCH | partial update | Yes |
| DELETE | remove | Yes |
| HEAD | headers only, no body | No |
| OPTIONS | discover allowed methods | No |

## Status code categories

| First digit | Category | Fault |
|---|---|---|
| 2xx | Success | — |
| 3xx | Redirection | — |
| 4xx | Client error | You/the request |
| 5xx | Server error | The server |

Memorize: `200` OK · `201` Created · `301`/`302` redirect · `400` bad request ·
`401` unauthorized (not logged in) · `403` forbidden (logged in, not allowed) ·
`404` not found · `405` method not allowed · `500` server exception.

## Key headers

| Header | Direction | Meaning |
|---|---|---|
| `Host` | request | which site |
| `User-Agent` | request | client identity |
| `Content-Type` | both | body format |
| `Authorization` | request | credentials/token |
| `Cookie` | request | send stored cookies back |
| `Set-Cookie` | response | ask browser to store a cookie |
| `Location` | response | where to redirect to |

## Cookies/sessions in one sentence

Server sets a `sessionid` cookie → browser auto-sends it on every future
request → server looks up session data by that ID. This is how "being
logged in" survives across stateless requests.

## HTML skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>...</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>...</header>
    <nav>...</nav>
    <main>
        <h1>...</h1>
        <form method="post" action="...">
            <input type="text" name="...">
            <button type="submit">Send</button>
        </form>
    </main>
    <footer>...</footer>
</body>
</html>
```

## CSS essentials

```css
* { box-sizing: border-box; }         /* padding/border inside declared width */

.class-selector { }
#id-selector    { }
tag-selector    { }

/* Flexbox — one dimension */
.row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Grid — two dimensions, responsive without media queries */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
}
```

## DevTools

`F12` → **Network** tab = inspect real requests/responses.
`F12` → **Elements** tab = inspect/live-edit HTML & CSS.
