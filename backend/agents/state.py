from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class WarRoomState(TypedDict):
    # Logs/Traces for the frontend
    logs: List[str]
    
    # Reports from individual agents
    release_notes: str
    analyst_report: str
    comms_report: str
    pm_draft: str
    critic_review: str
    
    # Final output JSON (matches Pydantic schema)
    final_output: Optional[Dict[str, Any]]
