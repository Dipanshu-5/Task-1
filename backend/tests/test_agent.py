import pytest
from datetime import date
from app.agents.graph import agent_graph
from app.tools.crm_tools import (
    summarize_and_extract_interaction_tool,
    generate_follow_up_suggestions_tool,
    log_interaction_tool,
    edit_interaction_tool
)

def test_extraction_tool():
    # Will run the Mock LLM internally due to mocked GROQ_API_KEY
    res = summarize_and_extract_interaction_tool("Met Dr. Priya to discuss efficacy")
    assert "extracted_data" in res
    assert "hcp_name" in res
    assert res["extracted_data"]["interaction_type"] == "In-Person"

def test_follow_up_suggestions_tool(db_session):
    res = generate_follow_up_suggestions_tool(
        db_session,
        sentiment="Positive",
        topics_discussed=["Product Efficacy"],
        outcomes="Asked for clinical trials",
        original_notes="Discussed studies"
    )
    assert "suggestions" in res
    assert "recommended_date" in res
    assert len(res["suggestions"]) > 0

def test_log_interaction_tool(db_session):
    data = {
        "hcp_id": 1,
        "interaction_type": "Virtual",
        "interaction_date": str(date.today()),
        "topics_discussed": ["Safety Profile"],
        "sentiment": "Neutral",
        "original_notes": "Call with Dr. Priya"
    }
    res = log_interaction_tool(db_session, data)
    assert res.get("success") is True
    assert "interaction_id" in res
    
    # Check duplicate prevention
    dup = log_interaction_tool(db_session, data)
    assert "error" in dup
    assert "Duplicate entry" in dup["error"]

def test_agent_chat_flow_missing_fields(db_session):
    # Missing HCP (hcp_id)
    initial_state = {
        "user_message": "Discussed clinical efficacy.",
        "chat_history": [],
        "extracted_data": {
            "interaction_type": "In-Person",
            "topics_discussed": ["Product Efficacy"]
        },
        "validation_errors": [],
        "missing_fields": [],
        "compliance_warnings": [],
        "tool_name": None,
        "tool_inputs": None,
        "requires_confirmation": False,
        "confirmation_status": None,
        "agent_reply": ""
    }
    config = {"configurable": {"db": db_session}}
    final_state = agent_graph.invoke(initial_state, config=config)
    assert "HCP Selection" in "".join(final_state["missing_fields"])
    assert final_state["requires_confirmation"] is False

def test_agent_chat_flow_requires_confirmation(db_session):
    # Fully populated details
    initial_state = {
        "user_message": "Met Dr. Priya, discussed product access.",
        "chat_history": [],
        "extracted_data": {
            "hcp_id": 1,
            "interaction_type": "In-Person",
            "topics_discussed": ["Pricing/Access"],
            "interaction_date": str(date.today())
        },
        "validation_errors": [],
        "missing_fields": [],
        "compliance_warnings": [],
        "tool_name": None,
        "tool_inputs": None,
        "requires_confirmation": False,
        "confirmation_status": None,
        "agent_reply": ""
    }
    config = {"configurable": {"db": db_session}}
    final_state = agent_graph.invoke(initial_state, config=config)
    
    assert len(final_state["missing_fields"]) == 0
    assert final_state["requires_confirmation"] is True
    assert final_state["tool_name"] == "log_interaction_tool"
    assert "confirm" in final_state["agent_reply"]

def test_agent_chat_flow_confirm(db_session):
    # State with pending log execution and approved confirmation
    initial_state = {
        "user_message": "Yes, save it",
        "chat_history": [],
        "extracted_data": {
            "hcp_id": 1,
            "interaction_type": "In-Person",
            "topics_discussed": ["Product Efficacy"],
            "interaction_date": str(date.today())
        },
        "validation_errors": [],
        "missing_fields": [],
        "compliance_warnings": [],
        "tool_name": "log_interaction_tool",
        "tool_inputs": {
            "hcp_id": 1,
            "interaction_type": "In-Person",
            "topics_discussed": ["Product Efficacy"],
            "interaction_date": str(date.today())
        },
        "requires_confirmation": True,
        "confirmation_status": "approved",
        "agent_reply": ""
    }
    config = {"configurable": {"db": db_session}}
    final_state = agent_graph.invoke(initial_state, config=config)
    
    # Tool executes, status finishes
    assert "Success" in final_state["agent_reply"]
    assert final_state["tool_name"] is None

def test_agent_chat_flow_cancel(db_session):
    initial_state = {
        "user_message": "cancel",
        "chat_history": [],
        "extracted_data": {
            "hcp_id": 1,
            "interaction_type": "In-Person"
        },
        "validation_errors": [],
        "missing_fields": [],
        "compliance_warnings": [],
        "tool_name": "log_interaction_tool",
        "tool_inputs": {},
        "requires_confirmation": True,
        "confirmation_status": "rejected",
        "agent_reply": ""
    }
    config = {"configurable": {"db": db_session}}
    final_state = agent_graph.invoke(initial_state, config=config)
    assert "discarded" in final_state["agent_reply"] or "Cancelled" in final_state["agent_reply"]
    assert final_state["extracted_data"] == {}
