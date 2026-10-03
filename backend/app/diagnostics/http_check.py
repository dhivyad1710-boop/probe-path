import time
import requests


def _failure(kind, exc):
    # Build the failure result while the exception is still in scope.
    return {"ok": False, "status_code": None, "response_time_ms": None,
            "location": None, "error_type": kind, "error": type(exc).__name__}


def check_http(url: str, timeout: float = 10):
    """Send one GET request. Redirects are NOT followed so we report what the
    server actually answered. Response time is measured with a monotonic timer
    and is None if no response was received."""
    start = time.perf_counter()
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=False,
                         headers={"User-Agent": "ProbePath/1.0"})
        ms = round((time.perf_counter() - start) * 1000)
        return {"ok": True, "status_code": r.status_code, "response_time_ms": ms,
                "location": r.headers.get("Location"), "error_type": None, "error": None}
    except requests.exceptions.SSLError as e:
        return _failure("ssl", e)
    except requests.exceptions.Timeout as e:
        return _failure("timeout", e)
    except requests.exceptions.ConnectionError as e:
        return _failure("connection", e)
    except requests.exceptions.RequestException as e:
        return _failure("other", e)
