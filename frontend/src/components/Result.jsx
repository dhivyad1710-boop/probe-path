const LABEL = { healthy: "Healthy", warning: "Warning", failed: "Failed", unknown: "Unknown" };
const ICON = { success: "✓", warning: "!", failed: "✗", info: "i" };

function yesNo(v) {
  if (v === null || v === undefined) return "Not checked";
  return v ? "Successful" : "Failed";
}

export default function Result({ data }) {
  return (
    <div className="result">
      <section>
        <h2>Service Status</h2>
        <div className={`status ${data.status}`}>
          <span className="dot">●</span> {LABEL[data.status]}
        </div>
        <table className="facts">
          <tbody>
            <tr><th>Target</th><td>{data.target}</td></tr>
            <tr><th>HTTP Status</th><td>{data.http_status ?? "No response"}</td></tr>
            <tr><th>Response Time</th><td>{data.response_time_ms != null ? `${data.response_time_ms} ms` : "N/A"}</td></tr>
            <tr><th>DNS Resolution</th><td>{yesNo(data.dns_ok)}</td></tr>
            <tr><th>Connectivity</th><td>{yesNo(data.connectivity_ok)}</td></tr>
          </tbody>
        </table>
      </section>

      <section>
        <h2>Diagnostic Evidence</h2>
        <ul className="evidence">
          {data.evidence.map((e, i) => (
            <li key={i} className={e.status}>
              <span className="icon">{ICON[e.status]}</span>
              <strong>{e.step}:</strong> {e.message}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Diagnosis</h2>
        <p>{data.diagnosis}</p>
        {data.possible_causes.length > 0 && (
          <>
            <p className="sub">Possible causes (not confirmed):</p>
            <ul>{data.possible_causes.map((c, i) => <li key={i}>{c}</li>)}</ul>
          </>
        )}
      </section>

      <section>
        <h2>Recommended Action</h2>
        <p>{data.recommendation}</p>
      </section>

      <section>
        <h2>Diagnostic Timeline</h2>
        <table className="timeline">
          <tbody>
            {data.timeline.map((t, i) => (
              <tr key={i}><td className="time">{t.timestamp}</td><td>{t.step}</td><td>{t.result}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
