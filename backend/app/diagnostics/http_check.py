import time
import requests


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
        kind = "ssl"
    except requests.exceptions.Timeout as e:
        kind = "timeout"
    except requests.exceptions.ConnectionError as e:
        kind = "connection"
    except requests.exceptions.RequestException as e:
        kind = "other"
    return {"ok": False, "status_code": None, "response_time_ms": None,
            "location": None, "error_type": kind, "error": type(e).__name__}
