from pydantic import BaseModel, Field
from typing import List, Literal

class ActionItem(BaseModel):
    action: str = Field(description="The specific action to be taken")
    owner: str = Field(description="The role or person responsible for this action (e.g., 'Data Team', 'Engineering')")

class RiskItem(BaseModel):
    risk: str = Field(description="Description of the risk")
    mitigation: str = Field(description="How to mitigate this risk")

class CommunicationPlan(BaseModel):
    internal_messaging: str = Field(description="Guidance for internal stakeholders")
    external_messaging: str = Field(description="Guidance for external/customer-facing comms")

class WarRoomDecision(BaseModel):
    decision: Literal['Proceed', 'Pause', 'Roll Back'] = Field(description="The final launch decision")
    rationale: str = Field(description="Key drivers for the decision, including metric references and feedback summary")
    risk_register: List[RiskItem] = Field(description="Top risks associated with this decision")
    action_plan_24_48h: List[ActionItem] = Field(description="Actions required in the next 24-48 hours")
    communication_plan: CommunicationPlan = Field(description="Internal and external messaging guidance")
    confidence_score: int = Field(ge=1, le=100, description="Confidence in this decision (1-100)")
    confidence_increase_factors: str = Field(description="What would increase the confidence score?")
