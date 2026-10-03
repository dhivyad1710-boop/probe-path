"""Rule-based diagnosis. Reads only the collected facts; never guesses beyond them.
Returns (status, diagnosis, possible_causes, recommendation)."""


def diagnose(validation_ok, dns, tcp, http):
    if not validation_ok:
        return ("unknown", "The URL could not be validated.", [],
                "Enter a full URL such as https://example.com")

    if dns and not dns["ok"]:
        return ("failed", "The hostname could not be resolved.",
                ["Invalid or misspelled hostname", "DNS configuration issue",
                 "Temporary DNS failure"],
                "Verify the hostname and DNS configuration.")

    if tcp and not tcp["ok"]:
        causes = {
            "timeout": ["Firewall or routing issue", "Host is down or overloaded",
                        "Wrong port"],
            "refused": ["Service not running on this port", "Wrong port",
                        "Firewall rejecting the connection"],
        }.get(tcp["reason"], ["Network issue", "Service unavailable"])
        return ("failed",
                "The hostname resolved, but a TCP connection could not be established.",
                causes, "Check that the service is running and the port is reachable.")

    if http is None:
        return ("unknown", "No HTTP check was performed.", [], "Further investigation required.")

    if not http["ok"]:
        t = http["error_type"]
        if t == "timeout":
            return ("failed", "The service did not respond within the configured timeout.",
                    ["Service unavailable", "Network issue", "Server overload",
                     "Firewall/routing issue"],
                    "Check network connectivity and service availability.")
        if t == "ssl":
            return ("failed", "The TLS/SSL handshake failed.",
                    ["Expired or invalid certificate", "Hostname/certificate mismatch",
                     "Server not configured for HTTPS on this port"],
                    "Inspect the certificate and the server's HTTPS configuration.")
        return ("failed", "The connection was made but the HTTP request failed.",
                ["Connection reset by server", "Protocol mismatch"],
                "Further investigation required. Check server logs.")

    c = http["status_code"]
    if 200 <= c < 300:
        return ("healthy", "The service responded successfully.", [],
                "No immediate action required.")
    if 300 <= c < 400:
        loc = f" to {http['location']}" if http.get("location") else ""
        return ("warning", f"The service redirected the request{loc}. This is not necessarily an error.",
                [], "Open the redirect target and confirm it is the expected destination.")
    if c == 401:
        return ("warning", "The server requires authentication.", [],
                "Provide valid credentials or check the authentication setup.")
    if c == 403:
        return ("warning", "The server understood the request but refused access.",
                ["Permissions or ACL rules", "IP restrictions", "WAF/firewall rule"],
                "Check access permissions and firewall/WAF rules.")
    if c == 404:
        return ("warning", "The server responded, but the requested resource was not found.",
                [], "Verify the URL path or endpoint.")
    if c == 500:
        return ("failed", "The server returned an internal error.",
                ["Application error", "Bad configuration or recent deployment"],
                "Check application logs and recent server-side changes.")
    if 500 <= c < 600:
        return ("failed", f"The server returned a server-side error (HTTP {c}).",
                ["Backend or gateway issue", "Overload or maintenance"],
                "Check server/gateway logs and service status.")
    if 400 <= c < 500:
        return ("warning", f"The server rejected the request (HTTP {c}).", [],
                "Review the request URL and parameters.")
    return ("unknown", f"Unexpected HTTP status {c}.", [], "Further investigation required.")
