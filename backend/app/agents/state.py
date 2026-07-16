from typing import List, Dict, Any, Optional, TypedDict

class AgentState(TypedDict):
    # Core inputs
    user_message: str
    chat_history: List[Dict[str, str]]
    
    # Internal agent/LLM outputs
    detected_intent: str
    extracted_data: Dict[str, Any]
    validation_errors: List[str]
    missing_fields: List[str]
    compliance_warnings: List[str]
    
    # Tool routing trackers
    tool_name: Optional[str]
    tool_inputs: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    
    # Confirmation flags
    requires_confirmation: bool
    confirmation_status: Optional[str]  # "approved", "rejected", None
    
    # Final output
    agent_reply: str
