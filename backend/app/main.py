import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .schemas import DiagnoseRequest, DiagnoseResponse
from .diagnostics.url_check import validate_url
from .diagnostics.network_check import check_dns, check_tcp
from .diagnostics.http_check import check_http
from .diagnostics.diagnosis import diagnose

TIMEOUT = float(os.getenv("PROBE_TIMEOUT_SECONDS", "10"))

app = FastAPI(title="ProbePath", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def bad_request(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request. Send JSON like {\"url\": \"https://example.com\"}."})


@app.exception_handler(Exception)
async def unexpected(request: Request, exc: Exception):
    # Never leak stack traces to the client.
    print("Unhandled error:", repr(exc))
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error while running the diagnostic."})


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/diagnose", response_model=DiagnoseResponse)
def run_diagnosis(req: DiagnoseRequest):
    timeline, evidence = [], []

    def log(step, result):
        timeline.append({"timestamp": datetime.now().strftime("%H:%M:%S"), "step": step, "result": result})

    def ev(step, status, message):
        evidence.append({"step": step, "status": status, "message": message})

    def finish(target, validation_ok, dns=None, tcp=None, http=None):
        status, text, causes, rec = diagnose(validation_ok, dns, tcp, http)
        log("Diagnosis generated", status)
        return {
            "target": target, "status": status,
            "http_status": http["status_code"] if http and http["ok"] else None,
            "response_time_ms": http["response_time_ms"] if http and http["ok"] else None,
            "dns_ok": dns["ok"] if dns else None,
            "connectivity_ok": tcp["ok"] if tcp else None,
            "diagnosis": text, "possible_causes": causes, "recommendation": rec,
            "evidence": evidence, "timeline": timeline,
        }

    # 1. URL validation
    ok, msg, parts = validate_url(req.url)
    log("URL validation", "valid" if ok else "invalid")
    ev("URL Validation", "success" if ok else "failed", msg)
    if not ok:
        return finish(req.url.strip(), False)
    host, port, url = parts["hostname"], parts["port"], parts["url"]

    # 2. DNS
    dns = check_dns(host, port)
    log("DNS resolution", "success" if dns["ok"] else "failed")
    if dns["ok"]:
        ev("DNS Resolution", "success", f"{host} resolved to {', '.join(dns['ips'][:3])}")
    else:
        ev("DNS Resolution", "failed", f"Could not resolve {host} ({dns['error']})")
        return finish(url, True, dns)

    # 3. TCP connectivity
    tcp = check_tcp(host, port, min(TIMEOUT, 5))
    log("Connectivity check", "success" if tcp["ok"] else "failed")
    if tcp["ok"]:
        ev("TCP Connection", "success", f"Connected to {host}:{port}")
    else:
        ev("TCP Connection", "failed", f"{tcp['error']} on {host}:{port}")
        return finish(url, True, dns, tcp)

    # 4. HTTP request
    http = check_http(url, TIMEOUT)
    log("HTTP request", "completed" if http["ok"] else http["error_type"])
    if http["ok"]:
        c = http["status_code"]
        ev("HTTP Request", "success" if c < 300 else ("failed" if c >= 500 else "warning"),
           f"Server returned HTTP {c}")
        ev("Response Time", "info", f"{http['response_time_ms']} ms (single request, redirects not followed)")
        if http.get("location"):
            ev("Redirect", "info", f"Location: {http['location']}")
    else:
        ev("HTTP Request", "failed", f"Request failed ({http['error_type']}: {http['error']})")
    return finish(url, True, dns, tcp, http)


# Serve the built React app when frontend/dist exists (single-service deployment).
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
