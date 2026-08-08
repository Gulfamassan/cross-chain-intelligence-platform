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

  // Sprint 13 Day 7 additions
  const [explanation, setExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);

  // Sprint 14 Day 6: Cross-chain wallet comparison
  const [compareWallet2, setCompareWallet2] = useState("");
  const [compareCsv2, setCompareCsv2] = useState("");
  const [compareChain2, setCompareChain2] = useState("polygon");
  const [compareResult, setCompareResult] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const runInvestigation = async () => {
    setLoading(true);
    setError("");
    setReport(null);
    setGraphUrl(null);
    setExplanation(null);

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

  // Sprint 13 Day 7: fetch explainability breakdown for the current wallet
  const viewExplanation = async () => {
    setExplanationLoading(true);
    try {
      const response = await fetch(`${API_BASE}/entity/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_address: wallet, chain }),
      });
      const data = await response.json();
      setExplanation(data);
    } catch (err) {
      setExplanation({ explanation: "Could not load explanation." });
    } finally {
      setExplanationLoading(false);
    }
  };

  // Sprint 13 Day 7: scroll to the existing Wallet Network graph section
  const scrollToGraph = () => {
    const graphEl = document.querySelector(".chart-box.wide");
    if (graphEl) graphEl.scrollIntoView({ behavior: "smooth" });
  };

  // Sprint 14 Day 6: compare current wallet against a second wallet
  const runComparison = async () => {
    setCompareLoading(true);
    setCompareResult(null);
    try {
      const response = await fetch(`${API_BASE}/hybrid/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wallet_1: wallet,
          wallet_2: compareWallet2,
          wallet_1_csv: csvPath,
          wallet_2_csv: compareCsv2,
          wallet_1_chain: chain,
          wallet_2_chain: compareChain2,
        }),
      });
      const data = await response.json();
      setCompareResult(data);
    } catch (err) {
      setCompareResult({ error: "Comparison failed. Check inputs." });
    } finally {
      setCompareLoading(false);
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

            {/* Sprint 13 Day 7: Entity Intelligence card */}
            <div className="card wide">
              <h2>Entity Intelligence</h2>
              <p><strong>Wallet Address:</strong> {report.wallet_summary.wallet}</p>
              <p><strong>Chain:</strong> {report.wallet_summary.chain}</p>
              <p><strong>Entity Type:</strong> {report.wallet_summary.entity_label}</p>
              <p><strong>Confidence:</strong> {Math.round(report.wallet_summary.entity_confidence * 100)}%</p>
              <p><strong>Evidence:</strong></p>
              <ul>
                {report.wallet_summary.entity_evidence.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
              <div className="entity-actions">
                <button onClick={scrollToGraph}>View Graph</button>
                <button onClick={viewExplanation} disabled={explanationLoading}>
                  {explanationLoading ? "Loading..." : "View Explanation"}
                </button>
              </div>
              {explanation && (
                <div className="explanation-box">
                  <p>{explanation.explanation}</p>
                  <ul>
                    {explanation.evidence && explanation.evidence.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

{/* Sprint 14 Day 6: Cross-Chain Wallet Comparison */}
            <div className="card wide">
              <h2>Compare With Another Wallet</h2>
              <div className="input-panel">
                <input
                  type="text"
                  placeholder="Second Wallet Address"
                  value={compareWallet2}
                  onChange={(e) => setCompareWallet2(e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Second Wallet CSV Path"
                  value={compareCsv2}
                  onChange={(e) => setCompareCsv2(e.target.value)}
                />
                <select value={compareChain2} onChange={(e) => setCompareChain2(e.target.value)}>
                  {SUPPORTED_CHAINS.filter((c) => c.active).map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <button onClick={runComparison} disabled={compareLoading}>
                  {compareLoading ? "Comparing..." : "Compare"}
                </button>
              </div>

              {compareResult && !compareResult.error && (
                <>
                  <p><strong>Confidence:</strong> {compareResult.confidence}% ({compareResult.classification})</p>

                  {compareResult.cross_chain_pair && compareResult.cross_chain_evidence && (
                    <div className="explanation-box">
                      <h3>Cross-Chain Evidence</h3>
                      <p><strong>Source Chain:</strong> {compareResult.wallet_1_chain}</p>
                      <p><strong>Destination Chain:</strong> {compareResult.wallet_2_chain}</p>
                      <p>
                        <strong>Bridge Evidence:</strong>{" "}
                        {compareResult.cross_chain_evidence.bridge_evidence_detected ? "Detected" : "Not Detected"}
                      </p>
                      <p><strong>Cross-Chain Score:</strong> {compareResult.cross_chain_evidence.score}</p>
                      <p>
                        <strong>Status:</strong>{" "}
                        {compareResult.cross_chain_evidence.available ? "Available" : "Unavailable"}
                      </p>
                    </div>
                  )}

                  <p><strong>Evidence:</strong></p>
                  <ul>
                    {compareResult.explanation.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </>
              )}
              {compareResult && compareResult.error && <p className="error">{compareResult.error}</p>}
            </div>
            
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