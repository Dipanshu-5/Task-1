import json
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.models.crm import HCP, Interaction
from app.schemas.crm import InteractionCreate, InteractionUpdate
from app.services import crm as services

def get_llm():
    if settings.GROQ_API_KEY == "mocked_key" or not settings.GROQ_API_KEY:
        class MockLLM:
            def invoke(self, messages, **kwargs):
                from langchain_core.messages import AIMessage
                
                prompt_text = "".join([m.content for m in messages])
                
                # Check for intent classification first
                if "primary intent" in prompt_text.lower() or "intent classifier" in prompt_text.lower():
                    user_msg = ""
                    try:
                        if 'user message: "' in prompt_text.lower():
                            user_msg = prompt_text.lower().split('user message: "')[1].split('"')[0]
                        elif 'user message: ' in prompt_text.lower():
                            user_msg = prompt_text.lower().split('user message: ')[1].split('\n')[0].strip('"')
                    except Exception:
                        pass
                    
                    user_msg = user_msg.lower().strip()
                    intent = "unknown"
                    
                    if any(x in user_msg for x in ["yes", "confirm", "save", "approve"]):
                        intent = "confirm"
                    elif any(x in user_msg for x in ["no", "cancel", "reject", "stop"]):
                        intent = "cancel"
                    elif any(x in user_msg for x in ["history", "timeline", "past", "recent"]):
                        intent = "retrieve_history"
                    elif any(x in user_msg for x in ["suggest", "follow", "next step"]):
                        intent = "suggest_follow_up"
                    elif any(x in user_msg for x in ["edit", "update", "correct"]):
                        intent = "edit_interaction"
                    elif any(x in user_msg for x in ["met", "visited", "log", "record", "discuss"]):
                        intent = "log_interaction"
                        
                    return AIMessage(content=json.dumps({"intent": intent}))
                
                # Check for extraction
                if "extract" in prompt_text.lower() or "conversational notes" in prompt_text.lower():
                    user_msg = ""
                    try:
                        if 'conversational notes:\n"' in prompt_text.lower():
                            user_msg = prompt_text.lower().split('conversational notes:\n"')[1].split('"')[0]
                        elif 'conversational notes: "' in prompt_text.lower():
                            user_msg = prompt_text.lower().split('conversational notes: "')[1].split('"')[0]
                        elif 'conversational notes:\n' in prompt_text.lower():
                            user_msg = prompt_text.lower().split('conversational notes:\n')[1].split('\n')[0].strip('"')
                    except Exception:
                        pass
                        
                    hcp_name = "Dr. Priya Sharma"
                    if user_msg and not any(x in user_msg.lower() for x in ["priya", "sharma", "dr", "doctor"]):
                        hcp_name = ""  # Return empty to simulate missing doctor fields
                        
                    extracted = {
                        "extracted_data": {
                            "interaction_type": "In-Person",
                            "topics_discussed": ["Product Efficacy"],
                            "materials_shared": ["Clinical Brochure"],
                            "samples_distributed": [{"product": "Product X", "quantity": 5}],
                            "sentiment": "Positive",
                            "outcomes": "Dr. Sharma was pleased with the efficacy data and asked for a follow-up brochure.",
                            "follow_up_actions": "Send the prescribing information sheet in 2 weeks.",
                            "follow_up_days": 14,
                            "ai_summary": "Met Dr. Sharma today to discuss efficacy and safety. She showed positive interest."
                        },
                        "hcp_name": hcp_name,
                        "compliance_warnings": []
                    }
                    return AIMessage(content=json.dumps(extracted))
                    
                # Check for follow-up suggestions
                if "follow-up" in prompt_text.lower() or "outcomes" in prompt_text.lower():
                    suggestions = {
                        "suggestions": [
                            "Email clinical trial publications regarding Product X efficacy.",
                            "Schedule a brief virtual follow-up call to answer prescribing questions."
                        ],
                        "recommended_days": 14
                    }
                    return AIMessage(content=json.dumps(suggestions))
                    
                # Check for sentiment
                if "sentiment" in prompt_text.lower() or "compliance" in prompt_text.lower():
                    return AIMessage(content=json.dumps({
                        "sentiment": "Positive",
                        "warnings": []
                    }))
                
                return AIMessage(content="Hello, I have processed your request.")
        return MockLLM()
    
    return ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=0.0
    )


# 1. Log Interaction Tool
def log_interaction_tool(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log a confirmed interaction in the SQL database.
    Validates required fields, checks for duplicate logging on same day.
    """
    hcp_id = data.get("hcp_id")
    interaction_date_str = data.get("interaction_date")
    
    if not hcp_id or not interaction_date_str:
        return {"error": "Missing required fields: hcp_id or interaction_date."}
    
    # Check if HCP exists
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        return {"error": f"HCP with ID {hcp_id} does not exist."}
        
    try:
        interaction_date = date.fromisoformat(str(interaction_date_str))
    except ValueError:
        return {"error": f"Invalid date format '{interaction_date_str}'. Use YYYY-MM-DD."}
        
    # Prevent duplicate submission: same doctor, same date
    existing = db.query(Interaction).filter(
        Interaction.hcp_id == hcp_id,
        Interaction.interaction_date == interaction_date
    ).first()
    
    if existing:
        return {
            "error": "Duplicate entry detected",
            "message": f"An interaction for {hcp.full_name} on {interaction_date} already exists.",
            "interaction_id": existing.id
        }
        
    # Map raw fields to schema
    attendees = data.get("attendees", [])
    if isinstance(attendees, str):
        attendees = [x.strip() for x in attendees.split(",") if x.strip()]
        
    topics = data.get("topics_discussed", [])
    materials = data.get("materials_shared", [])
    samples = data.get("samples_distributed", [])
    
    ai_summary = data.get("ai_summary")
    if not ai_summary and data.get("original_notes"):
        ai_summary = f"Summary: {data.get('original_notes')[:150]}..."
        
    create_schema = InteractionCreate(
        hcp_id=hcp_id,
        interaction_type=data.get("interaction_type", "In-Person"),
        interaction_date=interaction_date,
        interaction_time=data.get("interaction_time"),
        attendees=attendees,
        topics_discussed=topics,
        materials_shared=materials,
        samples_distributed=samples,
        sentiment=data.get("sentiment", "Neutral"),
        outcomes=data.get("outcomes"),
        follow_up_actions=data.get("follow_up_actions"),
        follow_up_date=data.get("follow_up_date"),
        original_notes=data.get("original_notes"),
        ai_summary=ai_summary,
        created_by=data.get("created_by", "System Rep"),
        status="Submitted"
    )
    
    db_interaction = services.create_interaction(db, create_schema)
    
    return {
        "success": True,
        "message": "Interaction saved successfully.",
        "interaction_id": db_interaction.id,
        "record": {
            "id": db_interaction.id,
            "hcp_id": db_interaction.hcp_id,
            "interaction_type": db_interaction.interaction_type,
            "interaction_date": str(db_interaction.interaction_date)
        }
    }


# 2. Edit Interaction Tool
def edit_interaction_tool(db: Session, interaction_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Locates an existing interaction by ID, validates changes, and saves changes.
    Tracks changed fields in audit database.
    """
    db_interaction = services.get_interaction(db, interaction_id)
    if not db_interaction:
        return {"error": f"Interaction with ID {interaction_id} not found."}
        
    # Map dates if present
    if "interaction_date" in updates and isinstance(updates["interaction_date"], str):
        try:
            updates["interaction_date"] = date.fromisoformat(updates["interaction_date"])
        except ValueError:
            return {"error": "Invalid interaction_date format."}
            
    if "follow_up_date" in updates and isinstance(updates["follow_up_date"], str):
        try:
            updates["follow_up_date"] = date.fromisoformat(updates["follow_up_date"])
        except ValueError:
            return {"error": "Invalid follow_up_date format."}
            
    update_schema = InteractionUpdate(**updates)
    updated = services.update_interaction(db, interaction_id, update_schema)
    
    return {
        "success": True,
        "message": "Interaction updated successfully.",
        "interaction_id": interaction_id,
        "record": {
            "id": updated.id,
            "hcp_id": updated.hcp_id,
            "sentiment": updated.sentiment,
            "topics_discussed": updates.get("topics_discussed", [])
        }
    }


# 3. Retrieve Interaction History Tool
def retrieve_interaction_history_tool(db: Session, hcp_id: int, limit: int = 5) -> Dict[str, Any]:
    """
    Retrieve recent interactions for a given HCP to render a history timeline.
    """
    interactions = services.get_hcp_interactions(db, hcp_id, limit)
    timeline = []
    
    for item in interactions:
        try:
            import json
            topics = json.loads(item.topics_discussed) if item.topics_discussed else []
        except:
            topics = item.topics_discussed
            
        timeline.append({
            "id": item.id,
            "interaction_type": item.interaction_type,
            "interaction_date": str(item.interaction_date),
            "sentiment": item.sentiment,
            "topics_discussed": topics,
            "ai_summary": item.ai_summary
        })
        
    return {
        "hcp_id": hcp_id,
        "timeline": timeline,
        "count": len(timeline)
    }


# 4. Generate Follow-Up Suggestions Tool
def generate_follow_up_suggestions_tool(db: Session, sentiment: str, topics_discussed: List[str], outcomes: str, original_notes: str) -> Dict[str, Any]:
    """
    Analyze outcomes, sentiment, and commitments to recommend next actions.
    Uses LLM for Life-sciences specialized actions.
    """
    llm = get_llm()
    prompt = f"""
    You are a life-sciences CRM copilot. Based on the following interaction details, generate exactly 2-3 specific, compliant follow-up action suggestions for a pharmaceutical field representative. Also recommend a follow-up timeframe in number of days.
    
    Interaction Details:
    - Sentiment: {sentiment}
    - Topics Discussed: {", ".join(topics_discussed)}
    - Outcomes: {outcomes}
    - Interaction Notes: {original_notes}
    
    Format your response as a strict JSON object with:
    {{
      "suggestions": ["suggestion 1", "suggestion 2"],
      "recommended_days": 14
    }}
    
    Make suggestions professional, compliant (no diagnostic claims, no medicine guarantees), and relevant.
    """
    
    try:
        messages = [
            SystemMessage(content="You are a CRM copilot. Output JSON only. Do not wrap in markdown code blocks."),
            HumanMessage(content=prompt)
        ]
        res = llm.invoke(messages)
        text = res.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            if text.startswith("json"):
                text = text.split("\n", 1)[1].strip()
        parsed = json.loads(text)
        
        rec_days = parsed.get("recommended_days", 14)
        rec_date = date.today() + timedelta(days=rec_days)
        
        return {
            "suggestions": parsed.get("suggestions", []),
            "recommended_date": str(rec_date),
            "is_ai_generated": True
        }
    except Exception as e:
        rec_date = date.today() + timedelta(days=14)
        return {
            "suggestions": [
                f"Follow up regarding discussed topics: {', '.join(topics_discussed)}.",
                "Provide product brochure and prescribing documentation."
            ],
            "recommended_date": str(rec_date),
            "is_ai_generated": True,
            "error": str(e)
        }


# 5. Summarize and Extract Interaction Tool
def summarize_and_extract_interaction_tool(text: str) -> Dict[str, Any]:
    """
    Convert conversational text into structured interaction fields.
    Also returns compliance validation alerts.
    """
    llm = get_llm()
    prompt = f"""
    You are an AI data extractor for a Life-Sciences CRM. Your task is to extract structured entities from the following interaction notes recorded by a medical representative.
    
    Conversational Notes:
    "{text}"
    
    Extract the following fields into a JSON object:
    - hcp_name (the name of the doctor mentioned)
    - interaction_type (MUST be one of: "In-Person", "Virtual", "Email", "Phone")
    - topics_discussed (list of strings. Choose from: "Product Efficacy", "Efficacy and Safety", "Clinical Trial Data", "Pricing/Access" or others mentioned)
    - materials_shared (list of brochures or documents mentioned)
    - samples_distributed (list of dicts containing 'product' and 'quantity' if mentioned)
    - sentiment (MUST be one of: "Positive", "Neutral", "Negative")
    - outcomes (brief outcome sentence)
    - follow_up_actions (specific action rep needs to take)
    - follow_up_days (estimated number of days for follow up, default to 14 if not mentioned)
    - ai_summary (a brief, compliant 1-2 sentence summary of the interaction)
    
    Also, scan for COMPLIANCE warnings:
    - Detect any unsupported promotional claims (e.g. "cures", "100% safe", "guaranteed outcome")
    - Detect missing patient consent if medical history is discussed
    - Return a list of warning strings if any issues are found.
    
    Format the response as a strict JSON object with this shape:
    {{
      "extracted_data": {{
         "interaction_type": "...",
         "topics_discussed": [...],
         "materials_shared": [...],
         "samples_distributed": [...],
         "sentiment": "...",
         "outcomes": "...",
         "follow_up_actions": "...",
         "follow_up_days": 14,
         "ai_summary": "..."
      }},
      "hcp_name": "...",
      "compliance_warnings": ["warning 1", ...]
    }}
    
    Ensure the JSON is correct. Output JSON only. Do not wrap in markdown code blocks.
    """
    
    try:
        messages = [
            SystemMessage(content="You are a CRM parser. Output JSON only. Do not wrap in markdown code blocks."),
            HumanMessage(content=prompt)
        ]
        res = llm.invoke(messages)
        res_text = res.content.strip()
        
        if res_text.startswith("```"):
            res_text = res_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            if res_text.startswith("json"):
                res_text = res_text.split("\n", 1)[1].strip()
                
        parsed = json.loads(res_text)
        return parsed
    except Exception as e:
        return {
            "extracted_data": {
                "interaction_type": "In-Person",
                "topics_discussed": [],
                "materials_shared": [],
                "samples_distributed": [],
                "sentiment": "Neutral",
                "outcomes": "",
                "follow_up_actions": "",
                "follow_up_days": 14,
                "ai_summary": f"Notes parsed: {text[:100]}..."
            },
            "hcp_name": "",
            "compliance_warnings": [f"Extraction failed to parse: {str(e)}"]
        }
