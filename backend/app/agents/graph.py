import json
import re
from datetime import date
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.tools.crm_tools import (
    get_llm,
    log_interaction_tool,
    edit_interaction_tool,
    retrieve_interaction_history_tool,
    generate_follow_up_suggestions_tool,
    summarize_and_extract_interaction_tool
)
from app.models.crm import HCP

# --- Node 1: Intent Detection ---
def intent_detection_node(state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
    msg = state["user_message"].lower().strip()
    
    # Strip punctuation for cleaner keyword checks
    clean_msg = re.sub(r'[^\w\s]', '', msg).strip()
    
    # Quick static overrides for basic conversational flow
    if clean_msg in ["yes", "y", "confirm", "approve", "save", "save it", "yes please", "yes save it", "yes do it"]:
        return {"detected_intent": "confirm", "confirmation_status": "approved"}
    if clean_msg in ["no", "n", "cancel", "reject", "stop", "abort"]:
        return {"detected_intent": "cancel", "confirmation_status": "rejected"}
        
    llm = get_llm()
    prompt = f"""
    Analyze the user's message to identify their primary intent in a life-sciences CRM system.
    
    User Message: "{state["user_message"]}"
    
    Identify which of the following intents fits best:
    - log_interaction (wants to record, log, save, or note a new interaction or meeting)
    - edit_interaction (wants to update, correct, modify an existing interaction)
    - retrieve_history (wants to see recent interactions, timeline, or past meetings with a doctor)
    - suggest_follow_up (wants suggestions on next steps, recommended tasks, or follow-up scheduling)
    - analyze_sentiment (wants to assess sentiment or compliance check on interaction notes)
    - cancel (wants to stop, cancel, reset the current conversation or logging process)
    - confirm (explicitly agreeing to save or confirm extracted fields)
    - unknown (generic greeting or unrelated question)
    
    Format the response as a strict JSON object:
    {{
      "intent": "log_interaction" | "edit_interaction" | "retrieve_history" | "suggest_follow_up" | "analyze_sentiment" | "cancel" | "confirm" | "unknown"
    }}
    
    Output JSON only. Do not wrap in markdown code blocks.
    """
    
    try:
        messages = [
            SystemMessage(content="You are an intent classifier. Output JSON only."),
            HumanMessage(content=prompt)
        ]
        res = llm.invoke(messages)
        res_text = res.content.strip()
        if res_text.startswith("```"):
            res_text = res_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            if res_text.startswith("json"):
                res_text = res_text.split("\n", 1)[1].strip()
        parsed = json.loads(res_text)
        return {"detected_intent": parsed.get("intent", "unknown")}
    except Exception:
        # Fallback keyword matching
        if "history" in clean_msg or "timeline" in clean_msg or "past" in clean_msg or "recent" in clean_msg:
            return {"detected_intent": "retrieve_history"}
        if "suggest" in clean_msg or "follow" in clean_msg or "next step" in clean_msg:
            return {"detected_intent": "suggest_follow_up"}
        if "edit" in clean_msg or "update" in clean_msg or "correct" in clean_msg:
            return {"detected_intent": "edit_interaction"}
        if "met" in clean_msg or "visited" in clean_msg or "log" in clean_msg or "record" in clean_msg or "discuss" in clean_msg:
            return {"detected_intent": "log_interaction"}
        return {"detected_intent": "unknown"}


# --- Node 2: Extract Info ---
def extraction_node(state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
    intent = state.get("detected_intent")
    
    if intent == "log_interaction":
        extracted = summarize_and_extract_interaction_tool(state["user_message"])
        
        # Merge previously extracted data
        merged_data = {**state.get("extracted_data", {})}
        new_data = extracted.get("extracted_data", {})
        for k, v in new_data.items():
            if v or k not in merged_data:
                merged_data[k] = v
                
        # Handle doctor matching
        hcp_name = extracted.get("hcp_name")
        if hcp_name and "hcp_id" not in merged_data:
            db = config.get("configurable", {}).get("db") if config else None
            if db:
                hcp = db.query(HCP).filter(HCP.full_name.ilike(f"%{hcp_name}%")).first()
                if hcp:
                    merged_data["hcp_id"] = hcp.id
                    merged_data["hcp_name"] = hcp.full_name
                    
        return {
            "extracted_data": merged_data,
            "compliance_warnings": extracted.get("compliance_warnings", [])
        }
    
    return {}


# --- Node 3: Validation and Missing Fields ---
def validation_node(state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
    intent = state.get("detected_intent")
    
    if intent == "log_interaction":
        data = state.get("extracted_data", {})
        missing = []
        errors = []
        
        # Mandatory fields
        if not data.get("hcp_id"):
            missing.append("HCP Selection (hcp_id)")
        if not data.get("interaction_type"):
            missing.append("Interaction Type")
        if not data.get("interaction_date"):
            # Set default today date to avoid blocking
            data["interaction_date"] = str(date.today())
            
        topics = data.get("topics_discussed", [])
        if not topics:
            missing.append("Topics Discussed")
            
        # Sentiment checking
        sentiment = data.get("sentiment")
        if sentiment not in ["Positive", "Neutral", "Negative"]:
            data["sentiment"] = "Neutral"
            
        # Determine if confirmation is needed
        requires_confirm = False
        tool_name = None
        tool_inputs = None
        
        if len(missing) == 0:
            requires_confirm = True
            tool_name = "log_interaction_tool"
            tool_inputs = data
            
        return {
            "missing_fields": missing,
            "validation_errors": errors,
            "requires_confirmation": requires_confirm,
            "tool_name": tool_name,
            "tool_inputs": tool_inputs,
            "extracted_data": data
        }
        
    elif intent == "edit_interaction":
        data = state.get("extracted_data", {})
        interaction_id = data.get("interaction_id") or state.get("tool_inputs", {}).get("interaction_id")
        
        if not interaction_id:
            # Fetch last interaction ID from DB for easy demo
            db = config.get("configurable", {}).get("db") if config else None
            if db:
                from app.models.crm import Interaction
                last_int = db.query(Interaction).order_by(Interaction.id.desc()).first()
                if last_int:
                    interaction_id = last_int.id
                    
        if not interaction_id:
            return {"agent_reply": "Please specify the ID of the interaction you want to edit.", "detected_intent": "unknown"}
            
        # Gather updates
        updates = {k: v for k, v in data.items() if k != "interaction_id"}
        if not updates:
            updates = summarize_and_extract_interaction_tool(state["user_message"]).get("extracted_data", {})
            updates = {k: v for k, v in updates.items() if v}
            
        return {
            "tool_name": "edit_interaction_tool",
            "tool_inputs": {"interaction_id": interaction_id, "updates": updates},
            "requires_confirmation": True
        }
        
    elif intent == "retrieve_history":
        hcp_id = state.get("extracted_data", {}).get("hcp_id")
        if not hcp_id:
            # Fallback to check if a doctor is mentioned
            db = config.get("configurable", {}).get("db") if config else None
            if db:
                hcp = db.query(HCP).first()  # Fallback to first doctor for demo
                if hcp:
                    hcp_id = hcp.id
                    
        if not hcp_id:
            return {"agent_reply": "Please select or mention an HCP to retrieve history.", "detected_intent": "unknown"}
            
        return {
            "tool_name": "retrieve_interaction_history_tool",
            "tool_inputs": {"hcp_id": hcp_id, "limit": 5}
        }
        
    elif intent == "suggest_follow_up":
        # Needs details to recommend
        data = state.get("extracted_data", {})
        return {
            "tool_name": "generate_follow_up_suggestions_tool",
            "tool_inputs": {
                "sentiment": data.get("sentiment", "Neutral"),
                "topics_discussed": data.get("topics_discussed", ["General"]),
                "outcomes": data.get("outcomes", ""),
                "original_notes": state["user_message"]
            }
        }
        
    return {}


# --- Node 4: Tool Execution ---
def tool_execution_node(state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
    tool_name = state.get("tool_name")
    tool_inputs = state.get("tool_inputs")
    db = config.get("configurable", {}).get("db") if config else None
    
    if not db:
        return {"agent_reply": "Error: Database session not configured for agent workflow."}
        
    if not tool_name or not tool_inputs:
        return {}
        
    result = {}
    if tool_name == "log_interaction_tool":
        result = log_interaction_tool(db, tool_inputs)
    elif tool_name == "edit_interaction_tool":
        result = edit_interaction_tool(db, tool_inputs["interaction_id"], tool_inputs["updates"])
    elif tool_name == "retrieve_interaction_history_tool":
        result = retrieve_interaction_history_tool(db, tool_inputs["hcp_id"], tool_inputs.get("limit", 5))
    elif tool_name == "generate_follow_up_suggestions_tool":
        result = generate_follow_up_suggestions_tool(
            db, 
            tool_inputs["sentiment"], 
            tool_inputs["topics_discussed"], 
            tool_inputs["outcomes"], 
            tool_inputs["original_notes"]
        )
        
    return {
        "tool_result": result,
        # Clear tool details once executed
        "tool_name": None,
        "tool_inputs": None
    }


# --- Node 5: Response Generation ---
def response_generation_node(state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
    intent = state.get("detected_intent")
    reply = ""
    
    if intent == "cancel" or state.get("confirmation_status") == "rejected":
        return {
            "agent_reply": "Cancelled. Action discarded and state reset.",
            "extracted_data": {},
            "requires_confirmation": False,
            "confirmation_status": None,
            "tool_name": None,
            "tool_inputs": None
        }

    # If tool was executed, generate response based on result
    tool_result = state.get("tool_result")
    if tool_result:
        if "error" in tool_result:
            reply = f"There was an error executing the action: {tool_result['error']}"
            if "message" in tool_result:
                reply += f"\nDetails: {tool_result['message']}"
        elif "success" in tool_result:
            msg_lower = tool_result.get("message", "").lower()
            if "save" in msg_lower or "log" in msg_lower:
                rec = tool_result["record"]
                reply = f"Success! Interaction logged successfully for HCP ID {rec['hcp_id']} on {rec['interaction_date']}. (ID: {tool_result['interaction_id']})"
            elif "update" in msg_lower or "edit" in msg_lower:
                reply = f"Success! Interaction ID {tool_result['interaction_id']} has been updated."
        elif "timeline" in tool_result:
            timeline = tool_result["timeline"]
            if not timeline:
                reply = "No recent interactions found for this HCP."
            else:
                reply = f"Here is the recent history timeline ({len(timeline)} interactions):\n"
                for idx, t in enumerate(timeline):
                    reply += f"- {t['interaction_date']} [{t['interaction_type']}]: {', '.join(t['topics_discussed'])} (Sentiment: {t['sentiment']})\n"
        elif "suggestions" in tool_result:
            suggs = tool_result["suggestions"]
            rec_date = tool_result.get("recommended_date")
            reply = "Based on the conversation outcomes, here are AI-generated follow-up recommendations:\n"
            for s in suggs:
                reply += f"- {s}\n"
            reply += f"\nRecommended follow-up date: {rec_date}"
            
        return {"agent_reply": reply, "tool_result": None}

    # If missing fields exist, prompt user for them
    missing = state.get("missing_fields", [])
    if missing and intent == "log_interaction":
        reply = f"I've extracted partial details from your message. To finish logging, please provide: {', '.join(missing)}."
        return {"agent_reply": reply}

    # If waiting for confirmation
    if state.get("requires_confirmation") and not state.get("confirmation_status"):
        reply = f"I've extracted the interaction details. Please confirm the details in the preview panel on the right or type 'Yes' to save it."
        return {"agent_reply": reply}
        
    if intent == "unknown":
        reply = "I'm here to help you log interactions, edit them, generate follow-up recommendations, or view doctor timeline history. How can I assist you today?"
        return {"agent_reply": reply}

    return {"agent_reply": "I processed your request, but no action was taken."}


# --- Conditional Routing Logic ---
def route_after_validation(state: AgentState) -> str:
    intent = state.get("detected_intent")
    
    if intent == "cancel" or state.get("confirmation_status") == "rejected":
        return "respond"
        
    # If it's a confirm action and we have pending tool inputs
    if intent == "confirm" and state.get("confirmation_status") == "approved":
        if state.get("tool_name"):
            return "execute_tool"
            
    # If tool is selected and no confirmation is needed, run immediately
    if state.get("tool_name") and not state.get("requires_confirmation"):
        return "execute_tool"
        
    return "respond"


# --- Graph Construction ---
def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Register Nodes
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("execute_tool", tool_execution_node)
    workflow.add_node("respond", response_generation_node)
    
    # Configure Flow
    workflow.set_entry_point("intent_detection")
    workflow.add_edge("intent_detection", "extraction")
    workflow.add_edge("extraction", "validation")
    
    # Conditional Edges
    workflow.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "execute_tool": "execute_tool",
            "respond": "respond"
        }
    )
    
    # Edge after tool execution leads to final response
    workflow.add_edge("execute_tool", "respond")
    workflow.add_edge("respond", END)
    
    return workflow.compile()

agent_graph = create_agent_graph()
