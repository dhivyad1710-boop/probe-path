# ProbePath: Interview Notes

## Concepts demonstrated
Python, FastAPI, REST APIs, HTTP status codes, DNS, TCP/sockets, timeouts, exception handling, rule-based troubleshooting, response-time measurement, React state/fetch, frontend/backend communication, dev proxy, Git/GitHub.

## 60-second explanation
"ProbePath is a troubleshooting tool I built for websites and HTTP services. You enter a URL, and a FastAPI backend checks in order: URL validity, DNS resolution, TCP connection, then the HTTP request with measured response time. Each step is recorded as evidence. A rule-based module then turns that evidence into a diagnosis and a recommended action, for example a 404 means check the path, a 500 means check application logs, a DNS failure means check the hostname and DNS config. I deliberately kept it deterministic and honest: it says 'possible cause' when it can't be certain. The React frontend shows status, evidence, diagnosis, recommendation and a timeline. I built it to practice the first-line support workflow of narrowing down where a failure occurs."

## 30-second explanation
"ProbePath is a Python/FastAPI and React tool that diagnoses a URL by checking DNS, TCP connectivity and the HTTP response, then gives a rule-based diagnosis with recommended next steps and the evidence behind it. It never invents data and is honest about uncertainty."

## 20 likely questions, short answers
1. **What does it do?** Runs DNS, TCP and HTTP checks on a URL and explains the result with evidence.
2. **Why separate DNS, TCP and HTTP checks?** To localise the failure layer: name resolution, network/port, or application.
3. **What is DNS?** It translates hostnames to IP addresses; I use `socket.getaddrinfo`.
4. **Difference between 401 and 403?** 401: authentication required. 403: understood but access refused.
5. **What does a 500 tell you?** The server was reached but the application failed; check logs and recent deployments. It doesn't reveal the exact cause.
6. **Why not follow redirects?** To report what the server actually returned; a 301/302 isn't an error.
7. **How do you measure response time?** `time.perf_counter()` (monotonic) around the request; `null` if no response.
8. **How do you handle timeouts?** `requests` timeout of 10 s, TCP timeout of 5 s; catch exceptions and report a timeout diagnosis.
9. **Why FastAPI?** Simple, fast, automatic validation with Pydantic and `/docs` for testing.
10. **What is Pydantic doing?** Defines and validates request/response shapes.
11. **Why `requests`, not async?** FastAPI runs sync endpoints in a thread pool; simpler for a beginner-friendly project.
12. **How do you avoid exposing stack traces?** Catch exceptions in checks plus a global exception handler returning a generic message.
13. **Why rule-based instead of AI?** Transparent, testable, deterministic; AI could only be an optional explanation layer.
14. **What does "connection refused" vs "timeout" suggest?** Refused: host reachable but nothing listening (or rejected). Timeout: packets dropped, e.g. firewall, routing, host down.
15. **How does React talk to the backend?** `fetch` POST to `/api/diagnose`; Vite proxy in dev, FastAPI serves the build in production.
16. **What is CORS and why not needed?** Browser cross-origin restriction; the proxy/same-origin serving avoids it.
17. **What is an SSRF risk here?** Users could make the server probe internal addresses; mitigate with IP blocklists, rate limits, auth.
18. **How did you test?** Local test server for 200/302/401/403/404/500/slow, plus invalid URL, DNS and refused cases.
19. **Limitations?** Basic checks only, single request, results depend on network location, no history.
20. **What would you add next?** Private-IP blocking, TLS certificate expiry check, retries/multiple samples, unit tests with pytest, optional AI explanation.

## AI assistance (honest answer)
"I used Claude as a coding assistant to scaffold the project and review ideas. I specified the requirements and design, ran and tested it myself, and I can explain every module, the diagnostic logic and the trade-offs."
