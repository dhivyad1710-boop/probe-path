import socket


def check_dns(hostname: str, port: int):
    """Resolve hostname. Returns dict(ok, ips, error)."""
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        ips = sorted({i[4][0] for i in infos})
        return {"ok": True, "ips": ips, "error": None}
    except socket.gaierror as e:
        return {"ok": False, "ips": [], "error": str(e)}
    except Exception as e:  # e.g. UnicodeError for odd hostnames
        return {"ok": False, "ips": [], "error": str(e)}


def check_tcp(hostname: str, port: int, timeout: float = 5):
    """Try a plain TCP connection. Returns dict(ok, reason, error)."""
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return {"ok": True, "reason": None, "error": None}
    except socket.timeout:
        return {"ok": False, "reason": "timeout", "error": "Connection timed out"}
    except ConnectionRefusedError:
        return {"ok": False, "reason": "refused", "error": "Connection refused"}
    except OSError as e:
        return {"ok": False, "reason": "other", "error": str(e)}
