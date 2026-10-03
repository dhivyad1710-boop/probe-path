// Netlify Function version of the ProbePath backend (same checks and rules as the Python app).
import dns from "node:dns/promises";
import net from "node:net";

export const config = { path: "/api/diagnose" };

const HTTP_TIMEOUT_MS = 8000;
const TCP_TIMEOUT_MS = 3000;

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

function isPrivate(ip) {
  return /^(127\.|10\.|0\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(ip) ||
    ["::1", "::"].includes(ip) || /^(fc|fd|fe80)/i.test(ip);
}

function validate(raw) {
  raw = (raw || "").trim();
  if (!raw) return { ok: false, msg: "Please enter a URL." };
  if (!raw.includes("://")) return { ok: false, msg: "URL must start with http:// or https://" };
  let u;
  try { u = new URL(raw); } catch { return { ok: false, msg: "The URL is not valid." }; }
  if (!["http:", "https:"].includes(u.protocol)) return { ok: false, msg: "Only http:// and https:// URLs are supported." };
  const port = Number(u.port) || (u.protocol === "https:" ? 443 : 80);
  return { ok: true, msg: "URL is valid", url: raw, host: u.hostname.replace(/^\[|\]$/g, ""), port };
}

function tcpCheck(host, port) {
  return new Promise((resolve) => {
    const s = net.connect({ host, port, timeout: TCP_TIMEOUT_MS });
    s.once("connect", () => { s.destroy(); resolve({ ok: true }); });
    s.once("timeout", () => { s.destroy(); resolve({ ok: false, reason: "timeout", error: "Connection timed out" }); });
    s.once("error", (e) => resolve({ ok: false, reason: e.code === "ECONNREFUSED" ? "refused" : "other", error: e.code === "ECONNREFUSED" ? "Connection refused" : e.message }));
  });
}

async function httpCheck(url) {
  const start = performance.now();
  try {
    const r = await fetch(url, { redirect: "manual", signal: AbortSignal.timeout(HTTP_TIMEOUT_MS), headers: { "User-Agent": "ProbePath/1.0" } });
    return { ok: true, status: r.status, ms: Math.round(performance.now() - start), location: r.headers.get("location") };
  } catch (e) {
    const code = e?.cause?.code || "";
    let type = "other";
    if (e.name === "TimeoutError" || e.name === "AbortError") type = "timeout";
    else if (/CERT|SSL|TLS|SELF_SIGNED/i.test(code)) type = "ssl";
    else if (code) type = "connection";
    return { ok: false, type, error: code || e.name };
  }
}

function diagnose(valid, d, t, h) {
  if (!valid) return ["unknown", "The URL could not be validated.", [], "Enter a full URL such as https://example.com"];
  if (d && !d.ok) return ["failed", "The hostname could not be resolved.", ["Invalid or misspelled hostname", "DNS configuration issue", "Temporary DNS failure"], "Verify the hostname and DNS configuration."];
  if (t && !t.ok) {
    const causes = t.reason === "refused" ? ["Service not running on this port", "Wrong port", "Firewall rejecting the connection"]
      : ["Firewall or routing issue", "Host is down or overloaded", "Wrong port"];
    return ["failed", "The hostname resolved, but a TCP connection could not be established.", causes, "Check that the service is running and the port is reachable."];
  }
  if (!h) return ["unknown", "No HTTP check was performed.", [], "Further investigation required."];
  if (!h.ok) {
    if (h.type === "timeout") return ["failed", "The service did not respond within the configured timeout.", ["Service unavailable", "Network issue", "Server overload", "Firewall/routing issue"], "Check network connectivity and service availability."];
    if (h.type === "ssl") return ["failed", "The TLS/SSL handshake failed.", ["Expired or invalid certificate", "Hostname/certificate mismatch", "Server not configured for HTTPS on this port"], "Inspect the certificate and the server's HTTPS configuration."];
    return ["failed", "The connection was made but the HTTP request failed.", ["Connection reset by server", "Protocol mismatch"], "Further investigation required. Check server logs."];
  }
  const c = h.status;
  if (c >= 200 && c < 300) return ["healthy", "The service responded successfully.", [], "No immediate action required."];
  if (c >= 300 && c < 400) return ["warning", `The service redirected the request${h.location ? " to " + h.location : ""}. This is not necessarily an error.`, [], "Open the redirect target and confirm it is the expected destination."];
  if (c === 401) return ["warning", "The server requires authentication.", [], "Provide valid credentials or check the authentication setup."];
  if (c === 403) return ["warning", "The server understood the request but refused access.", ["Permissions or ACL rules", "IP restrictions", "WAF/firewall rule"], "Check access permissions and firewall/WAF rules."];
  if (c === 404) return ["warning", "The server responded, but the requested resource was not found.", [], "Verify the URL path or endpoint."];
  if (c === 500) return ["failed", "The server returned an internal error.", ["Application error", "Bad configuration or recent deployment"], "Check application logs and recent server-side changes."];
  if (c >= 500) return ["failed", `The server returned a server-side error (HTTP ${c}).`, ["Backend or gateway issue", "Overload or maintenance"], "Check server/gateway logs and service status."];
  if (c >= 400) return ["warning", `The server rejected the request (HTTP ${c}).`, [], "Review the request URL and parameters."];
  return ["unknown", `Unexpected HTTP status ${c}.`, [], "Further investigation required."];
}

export default async (req) => {
  if (req.method !== "POST") return json({ detail: "Use POST with JSON like {\"url\": \"https://example.com\"}." }, 405);
  let body;
  try { body = await req.json(); } catch { return json({ detail: "Invalid request. Send JSON like {\"url\": \"https://example.com\"}." }, 422); }

  try {
    const timeline = [], evidence = [];
    const log = (step, result) => timeline.push({ timestamp: new Date().toISOString().slice(11, 19), step, result });
    const ev = (step, status, message) => evidence.push({ step, status, message });
    const finish = (target, valid, d, t, h) => {
      const [status, diagnosis, possible_causes, recommendation] = diagnose(valid, d, t, h);
      log("Diagnosis generated", status);
      return json({
        target, status,
        http_status: h?.ok ? h.status : null, response_time_ms: h?.ok ? h.ms : null,
        dns_ok: d ? d.ok : null, connectivity_ok: t ? t.ok : null,
        diagnosis, possible_causes, recommendation, evidence, timeline,
      });
    };

    const v = validate(body?.url);
    log("URL validation", v.ok ? "valid" : "invalid");
    ev("URL Validation", v.ok ? "success" : "failed", v.msg);
    if (!v.ok) return finish((body?.url || "").trim(), false);

    let d;
    try {
      const addrs = await dns.lookup(v.host, { all: true });
      d = { ok: true, ips: addrs.map((a) => a.address) };
    } catch (e) { d = { ok: false, error: e.code || e.message }; }
    log("DNS resolution", d.ok ? "success" : "failed");
    if (!d.ok) {
      ev("DNS Resolution", "failed", `Could not resolve ${v.host} (${d.error})`);
      return finish(v.url, true, d);
    }
    ev("DNS Resolution", "success", `${v.host} resolved to ${d.ips.slice(0, 3).join(", ")}`);

    // The hosted version must not probe internal networks (SSRF protection).
    if (process.env.ALLOW_PRIVATE !== "true" && d.ips.some(isPrivate)) {
      ev("Safety Check", "failed", "Private/internal addresses cannot be checked on the hosted version.");
      log("Safety check", "blocked");
      return finish(v.url, false);
    }

    const t = await tcpCheck(v.host, v.port);
    log("Connectivity check", t.ok ? "success" : "failed");
    if (!t.ok) {
      ev("TCP Connection", "failed", `${t.error} on ${v.host}:${v.port}`);
      return finish(v.url, true, d, t);
    }
    ev("TCP Connection", "success", `Connected to ${v.host}:${v.port}`);

    const h = await httpCheck(v.url);
    log("HTTP request", h.ok ? "completed" : h.type);
    if (h.ok) {
      ev("HTTP Request", h.status < 300 ? "success" : h.status >= 500 ? "failed" : "warning", `Server returned HTTP ${h.status}`);
      ev("Response Time", "info", `${h.ms} ms (single request, redirects not followed)`);
      if (h.location) ev("Redirect", "info", `Location: ${h.location}`);
    } else ev("HTTP Request", "failed", `Request failed (${h.type}: ${h.error})`);
    return finish(v.url, true, d, t, h);
  } catch (e) {
    console.error("Unhandled error:", e);
    return json({ detail: "Unexpected server error while running the diagnostic." }, 500);
  }
};
