import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import "./InvestigationDashboard.css";

const API_BASE = "http://127.0.0.1:8000";

const SUPPORTED_CHAINS = [
  { id: "ethereum", name: "Ethereum", active: true },
  { id: "polygon", name: "Polygon", active: true },
  { id: "arbitrum", name: "Arbitrum", active: true },
  { id: "bnb", name: "BNB Chain", active: false },
];

const RISK_COLORS = { Low: "#2ecc71", Medium: "#f39c12", High: "#e74c3c" };

function InvestigationDashboard() {
  const [wallet, setWallet] = useState("");
  const [csvPath, setCsvPath] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [report, setReport] = useState(null);
  const [graphUrl, setGraphUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runInvestigation = async () => {
    setLoading(true);
    setError("");
    setReport(null);
    setGraphUrl(null);

    try {
      await fetch(`${API_BASE}/build-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv_path: csvPath }),
      });

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

      // Wallet network graph bhi generate karte hain
      const graphResponse = await fetch(`${API_BASE}/graph/visualize`, { method: "POST" });
      const graphData = await graphResponse.json();
      setGraphUrl(graphData.url);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Timeline event counts (chart ke liye)
  const timelineChartData = report
    ? Object.entries(
        report.timeline.reduce((acc, event) => {
          acc[event.event_type] = (acc[event.event_type] || 0) + 1;
          return acc;
        }, {})
      ).map(([type, count]) => ({ type, count }))
    : [];

  // Risk distribution (single wallet ke liye simple breakdown)
  const riskChartData = report
    ? Object.entries(report.wallet_summary.risk_score !== null ? { Risk: report.wallet_summary.risk_score, Safe: 100 - report.wallet_summary.risk_score } : {}).map(
        ([name, value]) => ({ name, value })
      )
    : [];

  // Chain distribution (abhi single-chain hai, future multi-wallet ke liye ready)
  const chainChartData = report
    ? [{ chain: report.wallet_summary.chain, count: report.wallet_summary.transactions }]
    : [];

  return (
    <div className="dashboard">
      <h1>Multi-Chain Investigation Dashboard</h1>

      <div className="chains-grid">
        {SUPPORTED_CHAINS.map((c) => (
          <div key={c.id} className={`chain-card ${c.active ? "active" : "inactive"}`}>
            <span className="chain-name">{c.name}</span>
            <span className="chain-status">{c.active ? "Active" : "Coming Soon"}</span>
          </div>
        ))}
      </div>

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
        <select value={chain} onChange={(e) => setChain(e.target.value)}>
          {SUPPORTED_CHAINS.filter((c) => c.active).map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <button onClick={runInvestigation} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {report && (
        <>
          {/* Summary Stat Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Wallet Count</span>
              <span className="stat-value">{report.wallet_summary.graph_connections + 1}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Transactions</span>
              <span className="stat-value">{report.wallet_summary.transactions}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Community</span>
              <span className="stat-value">{report.wallet_summary.cluster || "N/A"}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Risk</span>
              <span className="stat-value" style={{ color: RISK_COLORS[report.wallet_summary.risk_level] || "#333" }}>
                {report.wallet_summary.risk_score}/100
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">AI Confidence</span>
              <span className="stat-value">{report.wallet_summary.has_ai_embedding ? "Available" : "N/A"}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Chain</span>
              <span className="stat-value">{report.wallet_summary.chain}</span>
            </div>
          </div>

          {/* Charts Section */}
          <div className="charts-section">
            <div className="chart-box">
              <h3>Timeline (Event Types)</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={timelineChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#2e5395" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-box">
              <h3>Risk Distribution</h3>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={riskChartData} dataKey="value" nameKey="name" outerRadius={70} label>
                    {riskChartData.map((entry, i) => (
                      <Cell key={i} fill={entry.name === "Risk" ? "#e74c3c" : "#2ecc71"} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-box">
              <h3>Chain Distribution</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chainChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="chain" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#81b29a" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-box wide">
              <h3>Wallet Network</h3>
              {graphUrl ? (
                <iframe
                  src={graphUrl}
                  title="Wallet Network Graph"
                  className="graph-iframe"
                />
              ) : (
                <p>Graph loading...</p>
              )}
            </div>
          </div>

          {/* Existing Cards */}
          <div className="cards-grid">
            <div className="card">
              <h2>Recommendation</h2>
              <p className="priority">{report.recommendation.priority}</p>
              <ul>
                {report.recommendation.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>

            <div className="card wide">
              <h2>Summary</h2>
              <p>{report.summary.text_summary}</p>
            </div>

            <div className="card wide">
              <h2>Timeline Details</h2>
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
        </>
      )}
    </div>
  );
}

export default InvestigationDashboard;