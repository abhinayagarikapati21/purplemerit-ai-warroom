import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [hasEntered, setHasEntered] = useState(false);
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [finalDecision, setFinalDecision] = useState(null);
  
  // Dynamic Data States
  const [latestMetrics, setLatestMetrics] = useState(null);
  const [recentFeedback, setRecentFeedback] = useState([]);
  
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (!hasEntered) return;

    // Fetch live dashboard data from the API on mount
    const fetchDashboardData = async () => {
      try {
        const metRes = await fetch('http://localhost:8000/api/data/metrics');
        const metData = await metRes.json();
        if (metData && metData.length > 0) {
          setLatestMetrics(metData[metData.length - 1]);
        }

        const fbRes = await fetch('http://localhost:8000/api/data/feedback');
        const fbData = await fbRes.json();
        if (fbData && fbData.length > 0) {
          const negatives = fbData.filter(f => f.rating < 3).slice(0, 4);
          setRecentFeedback(negatives);
        }
      } catch (err) {
        console.error("Error fetching mock data:", err);
      }
    };
    fetchDashboardData();
  }, [hasEntered]);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const runWarRoom = async () => {
    setIsRunning(true);
    setLogs([]);
    setFinalDecision(null);
    
    const eventSource = new EventSource('http://localhost:8000/api/war-room/run');

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'log') {
        setLogs(prev => [...prev, data.content]);
      } else if (data.type === 'final_decision') {
        setFinalDecision(data.content);
        eventSource.close();
        setIsRunning(false);
      } else if (data.type === 'error') {
        setLogs(prev => [...prev, `[ERROR] ${data.content}`]);
        eventSource.close();
        setIsRunning(false);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsRunning(false);
    };
  };

  if (!hasEntered) {
    return (
      <div className="landing-page">
        <div className="landing-card">
          <h1 className="landing-title">PurpleMerit</h1>
          <p className="landing-subtitle">Cross-Functional AI War Room Assessment</p>
          <button className="btn-enter" onClick={() => setHasEntered(true)}>
            Launch Agent Dashboard
          </button>
        </div>
      </div>
    );
  }

  // 2. Render Main Dashboard
  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>System Diagnostics</h1>
        <div className="status-badge">
          <div className="pulse"></div>
          Production V2.0 
        </div>
      </header>

      <div className="main-content">
        <div className="panel left-panel">
          <h2 className="panel-title">
            Live Telemetry <span className="live-indicator">ACTIVE</span>
          </h2>
          
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">p95 API Latency</div>
              <div className="metric-val trend-down">
                {latestMetrics ? `${latestMetrics.p95_api_latency_ms.toFixed(1)}ms` : 'Loading...'}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Payment Success</div>
              <div className="metric-val trend-down">
                {latestMetrics ? `${latestMetrics.payment_success_pct}%` : 'Loading...'}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Crash Rate Vol.</div>
              <div className="metric-val trend-down">
                {latestMetrics ? `${latestMetrics.crash_rate_pct}%` : 'Loading...'}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Overall DAU</div>
              <div className="metric-val">
                {latestMetrics ? latestMetrics.dau.toLocaleString() : 'Loading...'}
              </div>
            </div>
          </div>

          <div className="feedback-section">
             <div className="metric-label" style={{marginBottom: '0.8rem'}}>Recent User Reports</div>
             {recentFeedback.length > 0 ? recentFeedback.map((fb, idx) => (
               <div key={idx} className="feedback-item">
                 "{fb.content}"
               </div>
             )) : (
               <div className="feedback-item">Loading feedback stream...</div>
             )}
          </div>

          <button 
            className="btn-primary" 
            onClick={runWarRoom} 
            disabled={isRunning}>
            {isRunning ? 'Deploying War Room Agents...' : 'Initialize AI War Room'}
          </button>
        </div>

        <div className="panel right-panel">
          <h2 className="panel-title">Multi-Agent State & Decision Pipeline</h2>
          
          {finalDecision ? (
             <div className="final-decision-box">
                <h3 style={{margin: '0 0 1rem 0', fontWeight: '800'}}>Final Vector: 
                  <span className={`decision-${finalDecision.decision.split(' ')[0]}`}> {finalDecision.decision}</span>
                </h3>
                <p style={{fontSize: '1rem', lineHeight: '1.6'}}>
                  <strong>Rationale:</strong> {finalDecision.rationale}
                </p>
                <div className="json-view">
                  {JSON.stringify(finalDecision, null, 2)}
                </div>
             </div>
          ) : (
            <div className="log-box">
              {logs.length === 0 && <div style={{opacity: 0.5}}>Awaiting manual execution override...</div>}
              {logs.map((log, idx) => (
                <div key={idx} className="log-entry">
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
