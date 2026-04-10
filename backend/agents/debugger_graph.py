import os
import json
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from .debugger_state import DebuggerState, BugReportFinalOutput
from tools.execute_code import run_python_code
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)

def extract_text(response) -> str:
    content = getattr(response, 'content', str(response))
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join([item.get('text', str(item)) if isinstance(item, dict) else str(item) for item in content])
    return str(content)

# we use with_structured_output to force Gemini to return strict valid JSON
llm_json = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1).with_structured_output(BugReportFinalOutput)

def triage_agent(state: DebuggerState) -> Dict[str, Any]:
    trace = {"agent": "Triage", "action": "Analyzing user Bug Report..."}
    prompt = PromptTemplate.from_template(
        "You are an expert technical support engineer. Analyze the following bug report and logs.\n"
        "Extract the exact symptoms, the expected vs actual behavior, and relevant environment details.\n"
        "## Bug Report:\n{bug_report}\n\n## Logs:\n{logs}\n\n"
        "Summary:"
    )
    chain = prompt | llm
    summary = chain.invoke({"bug_report": state["bug_report"], "logs": state["logs"]})
    return {"triage_summary": extract_text(summary), "agent_traces": [trace]}

def log_analyst_agent(state: DebuggerState) -> Dict[str, Any]:
    trace = {"agent": "Log Analyst", "action": "Extracting error signatures from raw logs..."}
    prompt = PromptTemplate.from_template(
        "You are a forensic log analyst. Extract ONLY the relevant error lines or stack traces from the following logs that explain the crash.\n"
        "Ignore normal operational noise.\n\n## Logs:\n{logs}\n\nEvidence lines:"
    )
    chain = prompt | llm
    evidence = chain.invoke({"logs": state["logs"]})
    
    content_text = extract_text(evidence)
    evidence_list = [line.strip() for line in content_text.split('\n') if len(line.strip()) > 5]
    return {"extracted_evidence": evidence_list, "agent_traces": [trace]}

def reproduction_agent(state: DebuggerState) -> Dict[str, Any]:
    attempts = state.get("repro_attempts", 0) + 1
    trace1 = {"agent": "Reproduction", "action": f"Writing minimal executable python repro script (Attempt {attempts})..."}
    
    prompt = PromptTemplate.from_template(
        "You are a test automation engineer. Write a totally standalone Python script that reproduces the bug causing runtime exceptions.\n"
        "The script must crash or output an error that matches the original log evidence. It should mock or stub any unavailable data.\n"
        "Output ONLY raw python code. No markdown formatting, no explanations.\n\n"
        "## Bug Triage Summary:\n{triage_summary}\n\n"
        "## Required Error Evidence to reproduce:\n{extracted_evidence}\n\n"
        "## Previous Run Output (if retrying you must fix the code):\n{repro_results}\n\n"
    )
    chain = prompt | llm
    raw_code_resp = chain.invoke({
        "triage_summary": state.get("triage_summary", ""),
        "extracted_evidence": str(state.get("extracted_evidence", [])),
        "repro_results": state.get("repro_results", "None (First iteration)")
    })
    raw_code = extract_text(raw_code_resp)
    
    # Strip LLM markdown artifacts just in case
    clean_code = raw_code.replace("```python", "").replace("```", "").strip()
    
    trace2 = {"agent": "Reproduction Sandbox", "action": "Executing generated Python code in local secure subprocess..."}
    execution_result = run_python_code(clean_code)
    
    # Heuristic for if our script "failed" appropriately in a way simulating a bug
    success = "STDERR" in execution_result or "Exception" in execution_result or "Traceback" in execution_result
    
    trace3 = {"agent": "Reproduction Sandbox", "action": f"Code executed. Issue Reproduced: {'✅ TRUE' if success else '❌ FALSE'}"}
    
    return {
        "repro_script": clean_code, 
        "repro_results": execution_result, 
        "repro_success": success,
        "repro_attempts": attempts,
        "agent_traces": [trace1, trace2, trace3]
    }

def fix_planner_agent(state: DebuggerState) -> Dict[str, Any]:
    trace = {"agent": "Fix Planner", "action": "Formulating root cause and actionable patch plan..."}
    prompt = PromptTemplate.from_template(
        "You are a Senior Staff Engineer. Review the bug summary, log evidence, and the output of our verification script.\n"
        "Determine the root cause and propose a patch plan.\n\n"
        "## Triage Summary:\n{triage_summary}\n\n## Repro Output:\n{repro_results}\n\n"
        "Provide your proposed root cause and patch plan:"
    )
    chain = prompt | llm
    plan = chain.invoke({
        "triage_summary": state.get("triage_summary", ""), 
        "repro_results": state.get("repro_results", "")
    })
    
    return {
        "root_cause_proposal": "Hypothesis based on executed logs.", 
        "patch_plan_raw": extract_text(plan), 
        "agent_traces": [trace]
    }

def reviewer_agent(state: DebuggerState) -> Dict[str, Any]:
    trace = {"agent": "Reviewer", "action": "Critiquing patch plan and confirming bug reproduction integrity..."}
    
    prompt = PromptTemplate.from_template(
        "You are a strict code reviewer checking an agent's work.\n"
        "1. Did the repro script successfully trigger an error? (Success flag: {repro_success})\n"
        "2. Does the patch plan logically map to the runtime error output?\n\n"
        "Output EXACTLY 'PASS' if you approve. Anything else triggers a rejection and retry.\n\n"
        "## Patch Plan:\n{patch_plan_raw}\n\n"
        "## Repro Results:\n{repro_results}\n\n"
        "Decision:"
    )
    chain = prompt | llm
    decision_resp = chain.invoke({
        "repro_success": state.get("repro_success", False),
        "patch_plan_raw": state.get("patch_plan_raw", ""),
        "repro_results": state.get("repro_results", "")
    })
    decision_text = extract_text(decision_resp).strip()
    
    is_approved = decision_text.startswith("PASS")
    
    return {
        "is_approved": is_approved, 
        "reviewer_notes": decision_text, 
        "agent_traces": [trace]
    }

def finalizer_agent(state: DebuggerState) -> Dict[str, Any]:
    trace = {"agent": "Finalizer", "action": "Compiling data into final structured output constraint schema..."}
    
    prompt = PromptTemplate.from_template(
        "You are the final formatter. Your job is to take all accumulated intelligence and return EXACTLY the JSON schema requested.\n\n"
        "## Triage: {triage_summary}\n"
        "## Evidence: {extracted_evidence}\n"
        "## Repro Script: {repro_script}\n"
        "## Patch Decision: {patch_plan_raw}\n"
    )
    chain = prompt | llm_json
    final_output = chain.invoke({
        "triage_summary": state.get("triage_summary", ""),
        "extracted_evidence": str(state.get("extracted_evidence", [])),
        "repro_script": state.get("repro_script", ""),
        "patch_plan_raw": state.get("patch_plan_raw", ""),
    })
    
    return {
        # `.dict()` converts pydantic cleanly to a dict we can return to frontend
        "final_structured_output": final_output.dict(), 
        "agent_traces": [trace]
    }

def route_after_review(state: DebuggerState):
    """Router logic for the State Graph Loops."""
    if state["is_approved"]:
        return "finalizer_agent"
    elif state["repro_attempts"] >= state.get("max_repro_attempts", 3):
        print("Max attempts reached, forcing finalization.")
        return "finalizer_agent"
    else:
        return "reproduction_agent"

# Build Graph
builder = StateGraph(DebuggerState)

# Nodes
builder.add_node("triage_agent", triage_agent)
builder.add_node("log_analyst_agent", log_analyst_agent)
builder.add_node("reproduction_agent", reproduction_agent)
builder.add_node("fix_planner_agent", fix_planner_agent)
builder.add_node("reviewer_agent", reviewer_agent)
builder.add_node("finalizer_agent", finalizer_agent)

# Edges
builder.set_entry_point("triage_agent")
builder.add_edge("triage_agent", "log_analyst_agent")
builder.add_edge("log_analyst_agent", "reproduction_agent")
builder.add_edge("reproduction_agent", "fix_planner_agent")
builder.add_edge("fix_planner_agent", "reviewer_agent")
builder.add_conditional_edges("reviewer_agent", route_after_review)
builder.add_edge("finalizer_agent", END)

debugger_app = builder.compile()
