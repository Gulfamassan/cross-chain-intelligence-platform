import { useState } from "react";
import "./InvestigationDashboard.css";

const API_BASE = "http://127.0.0.1:8000";

function InvestigationDashboard() {
  const [wallet, setWallet] = useState("");
  const [csvPath, setCsvPath] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runInvestigation = async () => {
    setLoading(true);
    setError("");
    setReport(null);

    try {
      // Step 1: Pehle graph build karte hain
      await fetch(`${API_BASE}/build-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_path: csvPath }),
      });

      // Step 2: Intelligence report mangwate hain (summary, timeline, recommendation sab isi mein hain)
      const response = await fetch(`${API_BASE}/intelligence/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet, csv_path: csvPath, chain }),
      });

      if (!response.ok) {
        throw new Error("Investigation failed. Check wallet address and CSV path.");
      }

      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <h1>Investigation Dashboard</h1>

      <div className="input-panel">
        <input
          type="text"
          placeholder="Wallet Address"
          value={wallet}
          onChange={(e) => setWallet(e.target.value)}
        />
        <input
          type="text"
          placeholder="CSV Path (e.g. datasets/ethereum/0x....csv)"
          value={csvPath}
          onChange={(e) => setCsvPath(e.target.value)}
        />
        <input
          type="text"
          placeholder="Chain"
          value={chain}
          onChange={(e) => setChain(e.target.value)}
        />
        <button onClick={runInvestigation} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {report && (
        <div className="cards-grid">
          {/* Wallet Summary Card */}
          <div className="card">
            <h2>Wallet Summary</h2>
            <p>Transactions: {report.wallet_summary.transactions}</p>
            <p>Connections: {report.wallet_summary.graph_connections}</p>
            <p>Cluster: {report.wallet_summary.cluster || "N/A"}</p>
            <p>Centrality: {report.wallet_summary.centrality_score}</p>
          </div>

          {/* Risk Card */}
          <div className="card">
            <h2>Risk</h2>
            <p>
              {report.wallet_summary.risk_score !== null
                ? `${report.wallet_summary.risk_score}/100`
                : "Not yet calculated (Risk Engine pending)"}
            </p>
          </div>

          {/* AI Similarity Card */}
          <div className="card">
            <h2>AI Similarity</h2>
            <p>Embedding Available: {report.wallet_summary.has_ai_embedding ? "Yes" : "No"}</p>
            <p>Dimension: {report.wallet_summary.embedding_dimension}</p>
          </div>

          {/* Recommendation Card */}
          <div className="card">
            <h2>Recommendation</h2>
            <p className="priority">{report.recommendation.priority}</p>
            <ul>
              {report.recommendation.reasons.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          </div>

          {/* Summary Card */}
          <div className="card wide">
            <h2>Summary</h2>
            <p>{report.summary.text_summary}</p>
          </div>

          {/* Timeline Card */}
          <div className="card wide">
            <h2>Timeline</h2>
            <div className="timeline-list">
              {report.timeline.slice(0, 10).map((event, i) => (
                <div key={i} className="timeline-item">
                  <span className="timeline-date">{event.datetime}</span>
                  <span className="timeline-type">{event.event_type}</span>
                  <span className="timeline-value">{event.value_eth} ETH</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default InvestigationDashboard;