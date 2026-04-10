from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio

from agents.war_room import war_room_app
from agents.debugger_graph import debugger_app
from pydantic import BaseModel

class DebuggerInput(BaseModel):
    bug_report: str
    logs: str

from tools.metrics import get_metrics_data
from tools.sentiment import get_feedback_data

app = FastAPI(title="War Room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data/metrics")
def get_metrics():
    return get_metrics_data()

@app.get("/api/data/feedback")
def get_feedback():
    return get_feedback_data()

@app.get("/api/war-room/run")
async def run_war_room():
    """Run the war room graph and stream the execution traces and final result via SSE."""
    
    async def event_generator():
        initial_state = {"logs": []}
        
        # We run the synchronous LangGraph code locally, but LangGraph supports streaming
        # However, for simplicity and ensuring we capture all prints/state updates,
        # we can iterate over the graph stream.
        
        try:
            for event in war_room_app.stream(initial_state, stream_mode="values"):
                # `event` is the current State
                if "logs" in event and event["logs"]:
                    # Get the latest log that hasn't been yielded
                    # Actually, we can just yield the entire latest log list or just the last one.
                    latest_log = event["logs"][-1]
                    yield f"data: {json.dumps({'type': 'log', 'content': latest_log})}\n\n"
                    
                await asyncio.sleep(0.5) # Slight delay for UI effect
                
            # After graph finishes
            final_state = event
            if "final_output" in final_state and final_state["final_output"]:
                yield f"data: {json.dumps({'type': 'final_decision', 'content': final_state['final_output']})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/debugger/run")
async def run_debugger_workflow(payload: DebuggerInput):
    """Run the auto-debugger LangGraph and stream the real-time execution traces and final result via SSE."""
    
    async def event_generator():
        initial_state = {
            "bug_report": payload.bug_report,
            "logs": payload.logs,
            "repro_attempts": 0,
            "max_repro_attempts": 3,
            "agent_traces": []
        }
        
        try:
            for event in debugger_app.stream(initial_state, stream_mode="values"):
                if "agent_traces" in event and event["agent_traces"]:
                    # Get the most recently appended trace
                    latest_trace = event["agent_traces"][-1]
                    yield f"data: {json.dumps({'type': 'log', 'content': latest_trace})}\n\n"
                    
                await asyncio.sleep(0.3)
                
            final_state = event
            if "final_structured_output" in final_state and final_state["final_structured_output"]:
                yield f"data: {json.dumps({'type': 'final_decision', 'content': final_state['final_structured_output']})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
