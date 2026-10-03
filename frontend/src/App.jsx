import { useState } from "react";
import Result from "./components/Result.jsx";

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function diagnose(e) {
    e.preventDefault();
    if (!url.trim()) {
      setError("Please enter a URL to diagnose.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch("/api/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError((data && data.detail) || `The server returned an error (HTTP ${res.status}).`);
      } else {
        setResult(data);
      }
    } catch {
      setError("Unable to reach the diagnostic server. Please make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function clear() {
    setUrl("");
    setResult(null);
    setError("");
  }

  return (
    <div className="page">
      <header>
        <h1>ProbePath</h1>
        <p>IT Service Troubleshooting &mdash; Diagnose. Understand. Resolve.</p>
      </header>

      <form className="input-row" onSubmit={diagnose}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          aria-label="URL to diagnose"
        />
        <button type="submit" disabled={loading}>
          {result ? "Run Again" : "Diagnose Service"}
        </button>
        <button type="button" className="secondary" onClick={clear} disabled={loading}>
          Clear
        </button>
      </form>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Running checks (DNS, connection, HTTP)&hellip; this can take up to 15 seconds.</div>}
      {!loading && !result && !error && (
        <div className="empty">
          Enter a URL above to check DNS, connectivity and the HTTP response. Each step is recorded as evidence before a diagnosis is shown.
        </div>
      )}
      {result && <Result data={result} />}
    </div>
  );
}
