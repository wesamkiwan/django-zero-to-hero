# Demo: seeing raw HTTP with your own eyes

Django hides the raw protocol from you (that's the point of a framework), but
you should see it at least once, unfiltered, so "request" and "response"
stop being abstract words.

## Reproduce it yourself

Terminal 1 — start a dead-simple HTTP server serving a folder:

```bash
mkdir raw_http_test && cd raw_http_test
echo "<h1>Hello from a real server</h1>" > index.html
python -m http.server 8321
```

Terminal 2 — make a request and watch everything curl sends and receives:

```bash
curl -v http://127.0.0.1:8321/index.html
```

## What we captured running exactly that (real output, not made up)

```
> GET /index.html HTTP/1.1
> Host: 127.0.0.1:8321
> User-Agent: curl/8.18.0
> Accept: */*
>
< HTTP/1.0 200 OK
< Server: SimpleHTTP/0.6 Python/3.14.0
< Date: Thu, 16 Jul 2026 06:55:27 GMT
< Content-type: text/html
< Content-Length: 34
< Last-Modified: Thu, 16 Jul 2026 06:55:25 GMT
<
<h1>Hello from a real server</h1>
```

`>` lines are what the **client sent** (the request). `<` lines are what the
**server sent back** (the response). Map this to the lesson:

- `GET /index.html HTTP/1.1` — the **request line**: method, path, HTTP version.
- `Host`, `User-Agent`, `Accept` — **request headers**: metadata about the request.
- `HTTP/1.0 200 OK` — the **status line**: protocol version + status code + reason phrase.
- `Content-type`, `Content-Length` — **response headers**: metadata about the response body.
- The blank line — separates headers from the body.
- `<h1>Hello from a real server</h1>` — the **body**: the actual content.

This is exactly what your browser does every time it loads a page — just
with a graphical result instead of printed text. Open your browser's DevTools
(F12) → **Network** tab, reload any page, and click a request: you'll see
these same pieces (request headers, status code, response headers, body,
timing) presented visually.

## Try it yourself, then check what changes

- Request a path that doesn't exist (`/does-not-exist.html`) — what status
  code comes back?
- Add `-I` to curl (`curl -I ...`) — it sends a `HEAD` request (headers only,
  no body). Compare the output.
- Look at the `Date` and `Last-Modified` headers — these are exactly how
  browsers implement caching (`If-Modified-Since` — you'll meet this again
  when we add caching to Atlas in Module 12).
