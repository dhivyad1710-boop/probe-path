# ProbePath

**Diagnose. Understand. Resolve.**

A small IT service troubleshooting tool. Enter a URL and ProbePath runs basic checks (URL validation, DNS, TCP connection, HTTP request), shows the evidence it collected, and gives a rule-based diagnosis with a recommended next step.

## Why I built it
A practical utility inspired by basic application/system support workflows: when a site "is down", the first job is to work out *where* it fails (DNS, network, or the application) before fixing anything.

## Features
- URL validation (http/https only)
- DNS resolution and separate TCP connectivity check
- HTTP request with real response time (monotonic timer); redirects are reported, not followed
- Rule-based diagnosis for 2xx, 3xx, 401, 403, 404, 500, other 4xx/5xx, DNS failure, connection refused/timeout, HTTP timeout, TLS errors
- Evidence list and timeline, all from real checks (no fake data)
- Clean error messages; no stack traces reach the browser

## Architecture
`React → FastAPI (POST /api/diagnose) → Diagnostic checks → Rule-based diagnosis → JSON result`

```
backend/app/main.py                 endpoint, orchestration, timeline/evidence
backend/app/schemas.py              request/response models
backend/app/diagnostics/url_check.py, network_check.py, http_check.py, diagnosis.py
backend/tools/test_server.py        local server for 404/500/redirect/timeout tests
frontend/src/App.jsx, components/Result.jsx, styles.css
```

## Tech stack
React, Vite, Python, FastAPI, `requests`, standard-library `socket`.

## How it works
1. Validate the URL. 2. `socket.getaddrinfo` for DNS. 3. `socket.create_connection` for TCP. 4. `requests.get` with a timeout (10 s default) and no redirect following. 5. `diagnosis.py` maps the facts to a diagnosis and recommendation. If an early step fails, later steps are skipped, and the diagnosis says only what was observed.

## Installation
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cd ../frontend
npm install
```

## Running (development)
```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --port 8000
# terminal 2
cd frontend && npm run dev          # open http://localhost:5173
```
API docs: http://localhost:8000/docs

## Running / deploying as one service
```bash
cd frontend && npm run build        # creates frontend/dist
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```
FastAPI serves the built React app and the API together. On a host such as Render: build command `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build`, start command `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Read the SSRF note below before exposing it publicly.

## Testing (manual checklist)
Start the local test server: `cd backend && python tools/test_server.py` (port 9000).

| # | Case | Input | Expected |
|---|------|-------|----------|
| 1 | Healthy | `http://localhost:9000/ok` | Healthy, 200, response time shown |
| 2 | 404 | `http://localhost:9000/missing` | Warning, "resource was not found" |
| 3 | 500 | `http://localhost:9000/error` | Failed, "internal error" |
| 4 | Redirect | `http://localhost:9000/redirect` | Warning, redirect to /ok |
| 5 | 401 / 403 | `/unauthorized`, `/forbidden` | Warning with matching text |
| 6 | Invalid URL | `ftp://x` or `example` | Validation message, status Unknown |
| 7 | DNS failure | `https://no-such-host.invalid` | Failed, "hostname could not be resolved" |
| 8 | Timeout | `http://localhost:9000/slow` | Failed after ~10 s, timeout diagnosis |
| 9 | Connection refused | `http://localhost:9` | Failed, TCP connection failed |
| 10 | Empty input | (blank) | "Please enter a URL" |
| 11 | Backend unavailable | stop backend, click Diagnose | "Unable to reach the diagnostic server..." |

## Limitations
- Basic diagnostics only; it cannot determine every root cause. "Possible causes" are hints, not findings.
- Results depend on where the backend runs and on network conditions. A single request is not a performance benchmark.
- Not a replacement for enterprise monitoring tools; no history or alerting.
- **SSRF risk:** it will request any URL it is given, including internal addresses. Do not expose it publicly without blocking private IP ranges and adding rate limiting/auth.
- No optional AI explanation in v1; the diagnosis is fully deterministic.
