import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [hasEntered, setHasEntered] = useState(false);
  const [bugReport, setBugReport] = useState("Bug Title: App crashes when parsing JSON payload\nExpected: Returns 200 OK\nActual: 500 Internal Server Error.\nHints: Seems to happen only when `user_id` is passed as a string instead of an int.");
  const [logs, setLogs] = useState("INFO [2026-04-09]: Server started\nINFO: Handling request\nERROR: Traceback (most recent call last):\n  File \"/app/main.py\", line 42, in process_data\n    result = internal_math(user_id)\n  File \"/app/math.py\", line 10, in internal_math\n    return user_id / 2\nTypeError: unsupported operand type(s) for /: 'str' and 'int'");
  
  const [traces, setTraces] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [finalDecision, setFinalDecision] = useState(null);
  
  const tracesEndRef = useRef(null);

  const scrollToBottom = () => {
    tracesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom();
  }, [traces]);

  const runDebugger = async () => {
    setIsRunning(true);
    setTraces([]);
    setFinalDecision(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/debugger/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bug_report: bugReport, logs: logs })
      });

      if (!response.body) throw new Error("No readable stream");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        // The chunk might contain multiple "data: {...}\n\n" lines
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const dataStr = line.substring(6).trim();
              if(!dataStr) continue;
              const data = JSON.parse(dataStr);
              
              if (data.type === 'log') {
                setTraces(prev => [...prev, data.content]);
              } else if (data.type === 'final_decision') {
                setFinalDecision(data.content);
              } else if (data.type === 'error') {
                setTraces(prev => [...prev, { agent: "SYSTEM ERROR", action: data.content }]);
              }
            } catch (e) {
              console.error("Error parsing SSE JSON:", e, line);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setTraces(prev => [...prev, { agent: "NETWORK", action: "Failed to connect to backend stream." }]);
    } finally {
      setIsRunning(false);
    }
  };

  if (!hasEntered) {
    return (
      <div className="landing-page">
        <div className="landing-card">
          <h1 className="landing-title">Auto-Debugger</h1>
          <p className="landing-subtitle">Multi-Agent AI Triage & Patch Generation</p>
          <button className="btn-enter" onClick={() => setHasEntered(true)}>
            Initialize Diagnostics
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>PurpleMerit Auto-Debugger Dashboard</h1>
        <div className="status-badge">
          <div className={`pulse ${isRunning ? 'active' : ''}`}></div>
          {isRunning ? 'Agents Executing...' : 'System Idle'}
        </div>
      </header>

      <div className="main-content">
        <div className="panel left-panel">
          <h2 className="panel-title">Incident Inputs</h2>
          
          <div className="input-group">
            <label>1. Bug Report & Symptoms</label>
            <textarea 
              value={bugReport}
              onChange={(e) => setBugReport(e.target.value)}
              placeholder="Paste user bug report here..."
            />
          </div>

          <div className="input-group">
            <label>2. Raw System Logs</label>
            <textarea 
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              placeholder="Paste raw logs, stack traces, and system noise..."
              className="log-input"
            />
          </div>

          <button 
            className="btn-primary" 
            onClick={runDebugger} 
            disabled={isRunning || !bugReport || !logs}>
            {isRunning ? 'Deploying Triage Agents...' : 'Start Execution Graph'}
          </button>
        </div>

        <div className="panel right-panel">
          <h2 className="panel-title">LangGraph Execution Traces</h2>
          
          <div className="trace-box">
             {traces.length === 0 && <div className="placeholder-text">Awaiting input...</div>}
             {traces.map((trace, idx) => (
                <div key={idx} className={`trace-entry agent-${trace.agent.toLowerCase().replace(' ', '-')}`}>
                  <span className="agent-badge">{trace.agent}</span>
                  <span className="agent-action">{trace.action}</span>
                </div>
             ))}
             <div ref={tracesEndRef} />
          </div>

          {finalDecision && (
             <div className="final-decision-box fade-in">
                <h3>Final Deliverable: Structured Intelligence</h3>
                <div className="report-grid">
                  <div className="report-item">
                    <strong>Cause Hypothesis:</strong> {finalDecision.root_cause_hypothesis}
                  </div>
                  <div className="report-item">
                    <strong>Severity:</strong> {finalDecision.bug_summary?.severity}
                  </div>
                </div>
                
                <h4>Generated Patch Plan</h4>
                <div className="patch-plan">
                  <p><strong>Approach:</strong> {finalDecision.patch_plan?.approach}</p>
                  <p><strong>Risks:</strong> {finalDecision.patch_plan?.risks}</p>
                </div>

                <h4>Reproduction Script Used</h4>
                <pre className="code-block">
                  {finalDecision.repro_script}
                </pre>
             </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
