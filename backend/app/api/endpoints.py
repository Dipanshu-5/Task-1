from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.schemas import crm as schemas
from app.services import crm as services
from app.agents.graph import agent_graph
from app.tools.crm_tools import (
    summarize_and_extract_interaction_tool,
    generate_follow_up_suggestions_tool
)

router = APIRouter()

# HCP Endpoints
@router.get("/hcps", response_model=List[schemas.HCPResponse])
def read_hcps(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return services.get_hcps(db, skip=skip, limit=limit)

@router.post("/hcps", response_model=schemas.HCPResponse, status_code=status.HTTP_201_CREATED)
def create_hcp(hcp: schemas.HCPCreate, db: Session = Depends(deps.get_db)):
    return services.create_hcp(db, hcp)


# Interaction Endpoints
@router.get("/interactions", response_model=List[schemas.InteractionResponse])
def read_interactions(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return services.get_interactions(db, skip=skip, limit=limit)

@router.get("/interactions/{interaction_id}", response_model=schemas.InteractionResponse)
def read_interaction(interaction_id: int, db: Session = Depends(deps.get_db)):
    db_interaction = services.get_interaction(db, interaction_id)
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return db_interaction

@router.post("/interactions", response_model=schemas.InteractionResponse, status_code=status.HTTP_201_CREATED)
def create_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(deps.get_db)):
    hcp = services.get_hcp(db, interaction.hcp_id)
    if not hcp:
        raise HTTPException(status_code=400, detail="HCP not found")
    return services.create_interaction(db, interaction)

@router.patch("/interactions/{interaction_id}", response_model=schemas.InteractionResponse)
def update_interaction(interaction_id: int, updates: schemas.InteractionUpdate, db: Session = Depends(deps.get_db)):
    db_interaction = services.get_interaction(db, interaction_id)
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    updated = services.update_interaction(db, interaction_id, updates)
    return updated


# Timeline / History Endpoint
@router.get("/hcps/{hcp_id}/interaction-history", response_model=List[schemas.InteractionTimelineItem])
def read_hcp_interaction_history(hcp_id: int, limit: int = 10, db: Session = Depends(deps.get_db)):
    hcp = services.get_hcp(db, hcp_id)
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return services.get_hcp_interactions(db, hcp_id, limit)


# Agent Endpoints
@router.post("/agent/chat", response_model=schemas.AgentChatResponse)
async def agent_chat(payload: schemas.AgentChatRequest, db: Session = Depends(deps.get_db)):
    # Initialize LangGraph state
    initial_state = {
        "user_message": payload.message,
        "chat_history": payload.history or [],
        "extracted_data": payload.current_state.get("extracted_data", {}),
        "validation_errors": [],
        "missing_fields": [],
        "compliance_warnings": [],
        "tool_name": payload.current_state.get("tool_name"),
        "tool_inputs": payload.current_state.get("tool_inputs"),
        "requires_confirmation": payload.current_state.get("requires_confirmation", False),
        "confirmation_status": payload.current_state.get("confirmation_status"),
        "agent_reply": ""
    }
    
    config = {"configurable": {"db": db}}
    
    try:
        final_state = agent_graph.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")
        
    status_str = "active"
    if final_state.get("requires_confirmation") and not final_state.get("confirmation_status"):
        status_str = "requires_confirmation"
    elif final_state.get("detected_intent") == "confirm" and final_state.get("confirmation_status") == "approved":
        status_str = "completed"
    elif final_state.get("detected_intent") == "cancel":
        status_str = "completed"
        
    return schemas.AgentChatResponse(
        reply=final_state.get("agent_reply", ""),
        extracted_data=final_state.get("extracted_data", {}),
        confidence={"interaction_type": 0.95, "sentiment": 0.9},
        missing_fields=final_state.get("missing_fields", []),
        status=status_str
    )

@router.post("/agent/extract", response_model=schemas.AgentExtractResponse)
async def agent_extract(payload: schemas.AgentExtractRequest):
    extracted = summarize_and_extract_interaction_tool(payload.text)
    return schemas.AgentExtractResponse(
        extracted_data=extracted.get("extracted_data", {}),
        compliance_warnings=extracted.get("compliance_warnings", [])
    )

@router.post("/agent/follow-up-suggestions", response_model=schemas.AgentFollowUpResponse)
async def agent_follow_up_suggestions(payload: schemas.AgentFollowUpRequest, db: Session = Depends(deps.get_db)):
    if payload.interaction_id:
        interaction = services.get_interaction(db, payload.interaction_id)
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        import json
        try:
            topics = json.loads(interaction.topics_discussed) if interaction.topics_discussed else []
        except:
            topics = interaction.topics_discussed or []
            
        res = generate_follow_up_suggestions_tool(
            db, 
            interaction.sentiment,
            topics,
            interaction.outcomes or "",
            interaction.original_notes or ""
        )
    else:
        res = generate_follow_up_suggestions_tool(
            db,
            payload.sentiment or "Neutral",
            payload.topics_discussed or ["General"],
            payload.outcomes or "",
            payload.notes or ""
        )
        
    from datetime import date
    rec_date = None
    if "recommended_date" in res and res["recommended_date"]:
        try:
            rec_date = date.fromisoformat(res["recommended_date"])
        except ValueError:
            pass
            
    return schemas.AgentFollowUpResponse(
        suggestions=res.get("suggestions", []),
        recommended_date=rec_date,
        is_ai_generated=res.get("is_ai_generated", True)
    )
