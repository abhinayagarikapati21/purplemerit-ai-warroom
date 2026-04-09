<div align="center">
  <h1>🚀 PurpleMerit AI Agent War Room</h1>
  <p><strong>A Cross-Functional Multi-Agent Decision Engine for Product Operations</strong></p>
</div>

<br />

## 📖 System Overview

This repository contains a full-stack, stateful multi-agent system simulating a cross-functional "War Room" for rapid product launch evaluations. 

When a critical dashboard anomaly occurs, standard procedures often require hours of meetings between Data, Engineering, and Product teams. This project automates that deliberation using **LangGraph** orchestration. 

It synthesizes live telemetry data, categorizes raw user feedback, and enforces a rigid conflict-resolution workflow between autonomous AI personas to output a structured **Go/No-Go Decision JSON**—complete with action ownership and risk mitigation plans.

---

## 🧠 The Agent Orchestration Pipeline

The system utilizes a Supervisor/Coordinator pattern via **LangGraph**, ensuring a strict separation of responsibilities:

1. **Coordinator Architect:** Manages execution state, routes telemetry, and enforces the final Pydantic JSON schema constraints.
2. **Data Analyst Agent:** Evaluates raw time-series metrics. Automatically detects mathematical anomalies (e.g. latency spikes, drop-offs) over the last 14 days.
3. **Marketing & Comms Agent:** Processes unstructured feedback streams to evaluate real-time customer sentiment.
4. **Product Manager (PM) Agent:** Absorbs the data and sentiment reports, weighs them against known release risks, and drafts the initial operational proposal.
5. **Risk/Critic Agent:** An aggressive challenger node. It parses the PM's draft and actively looks for missing mitigation plans or overly optimistic assumptions, forcing a revision before the final output is generated.

---

## 🛠 Setup & Launch Instructions

### 1. Backend API (FastAPI + LangGraph)
1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure API Keys:
   - Create a file named `.env` in the `backend/` folder.
   - Add your Gemini API Key: `GEMINI_API_KEY=your_key_here`
5. Generate the Mock Dashboard Data (run once):
   ```bash
   python generate_mock_data.py
   ```
6. Start the API Server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### 2. Frontend Command Center (React/Vite)
1. Open a new terminal and navigate to the `ui` directory:
   ```bash
   cd ui
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dashboard:
   ```bash
   npm run dev
   ```

Open `http://localhost:5173` in your browser. Click the **"Initialize AI War Room"** button to start the multi-agent stream and generate the structured operational decision. 
