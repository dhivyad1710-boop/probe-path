from urllib.parse import urlparse


def validate_url(raw: str):
    """Return (ok, message, parts). parts = dict(url, scheme, hostname, port)."""
    raw = (raw or "").strip()
    if not raw:
        return False, "Please enter a URL.", None
    if "://" not in raw:
        return False, "URL must start with http:// or https://", None
    try:
        p = urlparse(raw)
        port = p.port  # raises ValueError if the port is invalid
    except ValueError:
        return False, "The URL is not valid (check the port number).", None
    if p.scheme not in ("http", "https"):
        return False, "Only http:// and https:// URLs are supported.", None
    if not p.hostname:
        return False, "The URL has no hostname.", None
    if port is None:
        port = 443 if p.scheme == "https" else 80
    return True, "URL is valid", {
        "url": raw, "scheme": p.scheme, "hostname": p.hostname, "port": port,
    }
