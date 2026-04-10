import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# Import State and Schema
from agents.state import WarRoomState
from api.schema import WarRoomDecision

# Import Tools
from tools.metrics import analyze_metric_trends, detect_anomalies, get_release_notes
from tools.sentiment import aggregate_user_sentiment

load_dotenv()

# We use Gemini for the agents
# Make sure to set GEMINI_API_KEY in .env
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
llm_strict = llm.with_structured_output(WarRoomDecision)

def log_event(state: WarRoomState, message: str):
    print(f"\n[TRACE] {message}")
    if "logs" not in state or state["logs"] is None:
        state["logs"] = []
    state["logs"].append(message)

def init_node(state: WarRoomState):
    log_event(state, "Coordinator Agent: Convening War Room...")
    notes = get_release_notes()
    log_event(state, f"Coordinator Agent: Loaded Release Notes. V2.0 Checkout Flow Revamp rollout initiated 10 days ago.")
    return {"release_notes": notes, "logs": state.get("logs", [])}

def data_analyst_node(state: WarRoomState):
    log_event(state, "Data Analyst Agent: Analyzing metric trends and anomalies...")
    trends = analyze_metric_trends()
    anomalies = detect_anomalies()
    
    prompt = f"""You are the Data Analyst. Based on the following tools output, summarize the quantitative health of the launch.
Trends: {trends}
Anomalies: {anomalies}

Provide a concise 3-paragraph report on the metrics, highlighting any major red flags."""
    
    response = llm.invoke([SystemMessage(content="You are a data analyst."), HumanMessage(content=prompt)])
    log_event(state, f"Data Analyst Agent: Report generated. Identified anomalies: {anomalies.strip()}")
    return {"analyst_report": response.content}

def comms_node(state: WarRoomState):
    log_event(state, "Marketing/Comms Agent: Analyzing user sentiment and feedback...")
    sentiment = aggregate_user_sentiment()
    
    prompt = f"""You are the Marketing/Comms Lead. Based on the following feedback aggregation, summarize customer perception.
Sentiment: {sentiment}

Provide a concise 2-paragraph report. Are users upset? What are the core complaints?"""
    
    response = llm.invoke([SystemMessage(content="You are a Comms Lead."), HumanMessage(content=prompt)])
    log_event(state, "Marketing/Comms Agent: Sentiment analysis complete. Heavy negative feedback regarding payments detected.")
    return {"comms_report": response.content}

def pm_node(state: WarRoomState):
    log_event(state, "Product Manager Agent: Synthesizing data and drafting launch decision...")
    prompt = f"""You are the Product Manager. Review the release notes, data report, and comms report.
Release Notes: {state['release_notes']}
Data Analyst Report: {state['analyst_report']}
Comms Report: {state['comms_report']}

Decide whether to Proceed, Pause, or Roll Back. Draft your proposed decision and rationale.
Be objective and weigh the risks."""

    response = llm.invoke([SystemMessage(content="You are the PM."), HumanMessage(content=prompt)])
    log_event(state, "Product Manager Agent: Draft decision formulated.")
    return {"pm_draft": response.content}

def critic_node(state: WarRoomState):
    log_event(state, "Risk/Critic Agent: Reviewing PM's draft decision...")
    prompt = f"""You are the strict Risk/Critic Agent. Review the PM's draft decision based on the underlying reports.
    
PM Draft: {state['pm_draft']}

Data Context: {state['analyst_report']}
Comms Context: {state['comms_report']}

Challenge their assumptions. If they chose to Proceed despite high crash rates or payment failures, call them out and suggest a Pause or Rollback. Output your critique."""

    response = llm.invoke([SystemMessage(content="You are the Risk Critic."), HumanMessage(content=prompt)])
    log_event(state, "Risk/Critic Agent: Critique provided. Highlighting immediate risks.")
    return {"critic_review": response.content}

def coordinator_node(state: WarRoomState):
    log_event(state, "Coordinator Agent: Finalizing official structured decision JSON based on War Room consensus...")
    prompt = f"""You are the War Room Coordinator. Synthesize the final decision based on the PM's draft and the Critic's review.
    
PM Draft: {state['pm_draft']}
Critic Review: {state['critic_review']}
Release Context: {state['release_notes']}

Output a strictly formatted decision JSON matching the required schema. Ensure the action plan includes mitigations for the risks highlighted by the critic."""

    # Use structured output
    response = llm_strict.invoke([SystemMessage(content="You are the orchestrator."), HumanMessage(content=prompt)])
    
    log_event(state, f"Coordinator Agent: Final decision is [ {response.decision} ].")
    
    # Store as dict
    final_output = response.dict()
    return {"final_output": final_output}

# Build Graph
workflow = StateGraph(WarRoomState)

workflow.add_node("init", init_node)
workflow.add_node("data_analyst", data_analyst_node)
workflow.add_node("comms", comms_node)
workflow.add_node("pm", pm_node)
workflow.add_node("critic", critic_node)
workflow.add_node("coordinator", coordinator_node)

workflow.add_edge(START, "init")
workflow.add_edge("init", "data_analyst")
workflow.add_edge("init", "comms")
workflow.add_edge("data_analyst", "pm")
workflow.add_edge("comms", "pm")
workflow.add_edge("pm", "critic")
workflow.add_edge("critic", "coordinator")
workflow.add_edge("coordinator", END)

war_room_app = workflow.compile()
