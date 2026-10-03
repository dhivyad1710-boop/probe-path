# ProbePath

**Diagnose. Understand. Resolve.**

ProbePath is a lightweight IT service troubleshooting tool. Enter a URL and it runs a sequence of basic checks (URL validation, DNS, TCP connection, HTTP request), records the evidence from each step, and produces a rule-based diagnosis with a recommended next action.

**Live demo:** _add your Netlify link here_
**Backend API:** _add your Render link here_ (`/docs` shows the API)

![ProbePath screenshot](docs/screenshot.png)
<!-- Take a screenshot of a result (e.g. https://example.com), save it as docs/screenshot.png -->

## Why I built it

When a website or service "is down", the first support task is working out *where* it fails: DNS, the network path, or the application itself. I built ProbePath as a practical utility around that basic first-line support workflow, and to practise Python, REST APIs, HTTP and networking fundamentals.

## Features

- URL validation (only `http://` and `https://` accepted)
- DNS resolution and a separate TCP connectivity check, so the failing layer can be identified
- HTTP request with real response time (monotonic timer); redirects are reported, not followed
- Rule-based diagnosis for 2xx, 3xx, 401, 403, 404, 500, other 4xx/5xx, DNS failure, connection refused/timeout, HTTP timeout and TLS errors
- Evidence list and timeline built only from checks actually performed (no fake data)
- "Possible cause" wording where the root cause cannot be confirmed
- Clean error messages; stack traces never reach the browser

## Architecture

```
React (Vite)  →  FastAPI  POST /api/diagnose  →  Diagnostic checks  →  Rule-based diagnosis  →  JSON result
```

```
backend/app/main.py                  API endpoint, runs checks in order, builds evidence + timeline
backend/app/schemas.py               Pydantic request/response models
backend/app/diagnostics/url_check.py       URL validation
backend/app/diagnostics/network_check.py   DNS (getaddrinfo) and TCP (create_connection)
backend/app/diagnostics/http_check.py      HTTP request, status code, response time
backend/app/diagnostics/diagnosis.py       Rules: evidence -> diagnosis + recommendation
backend/tools/test_server.py         Local server for 404/500/redirect/timeout testing
frontend/src/                        React UI (App.jsx, components/Result.jsx, styles.css)
```

## Tech stack

React, Vite, Python, FastAPI, Pydantic, `requests`, Python `socket` module, plain CSS.

## How it works

1. Validate the URL.
2. Resolve the hostname with `socket.getaddrinfo`.
3. Open a TCP connection with `socket.create_connection` (5 s timeout).
4. Send one HTTP GET with `requests` (10 s timeout, redirects not followed) and time it.
5. `diagnosis.py` maps the collected facts to a status (healthy / warning / failed / unknown), a diagnosis and a recommendation.

If an early step fails, later steps are skipped and the diagnosis only states what was observed.

## Installation

Requires Python 3.10+, Node.js 18+ and Git.

```bash
git clone https://github.com/YOUR-USERNAME/probe-path.git
cd probe-path

cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

## Running locally

Single service (FastAPI serves the built frontend):

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --port 8000
```

Open http://localhost:8000.

Or development mode with two terminals:

```bash
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev        # http://localhost:5173 (proxies /api to port 8000)
```

## Deployment

- **Backend (Render):** build `pip install -r backend/requirements.txt`, start `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend (Netlify):** base directory `frontend`, build `npm run build`, publish `frontend/dist`. Add `frontend/public/_redirects` containing `/api/*  https://YOUR-BACKEND.onrender.com/api/:splat  200` so Netlify forwards API calls to the backend.

The free Render tier sleeps when idle, so the first request can take about 30 seconds.

## Testing

Manual checklist. Start the local test server first: `cd backend && python tools/test_server.py` (port 9000). Use `127.0.0.1` rather than `localhost`: `localhost` may try IPv6 (`::1`) first and add seconds of delay on some systems.

| # | Case | Input | Expected |
|---|------|-------|----------|
| 1 | Healthy | `http://127.0.0.1:9000/ok` | Healthy, 200, response time in ms |
| 2 | Not found | `http://127.0.0.1:9000/missing` | Warning, 404 |
| 3 | Server error | `http://127.0.0.1:9000/error` | Failed, 500 |
| 4 | Redirect | `http://127.0.0.1:9000/redirect` | Warning, 302 to /ok |
| 5 | Auth | `/unauthorized`, `/forbidden` | Warning, 401 / 403 |
| 6 | Invalid URL | `ftp://x` or `example` | Validation message, status Unknown |
| 7 | DNS failure | `https://no-such-host.invalid` | Failed, hostname could not be resolved |
| 8 | Timeout | `http://127.0.0.1:9000/slow` | Failed after ~10 s, response time N/A |
| 9 | Connection refused | `http://127.0.0.1:9` | Failed, TCP connection failed |
| 10 | Empty input | (blank) | "Please enter a URL" |
| 11 | Backend unavailable | stop backend, click Diagnose | "Unable to reach the diagnostic server..." |

## Limitations

- Basic diagnostics only; it cannot determine every root cause. "Possible causes" are hints, not findings.
- Results depend on where the backend runs and on network conditions. A single request is not a performance benchmark.
- Not a replacement for enterprise monitoring tools; no history, alerting or authentication.
- **SSRF risk:** it requests any URL it is given, including internal addresses. A public deployment should block private IP ranges and add rate limiting.
- No automated tests yet; testing is manual (see above).

## Possible improvements

Private-IP blocking and rate limiting, TLS certificate expiry check, multiple samples per check, pytest unit tests for `diagnosis.py`.
