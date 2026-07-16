from pydantic import BaseModel, field_validator, Field
from datetime import date, time, datetime
from typing import List, Optional, Any
import json

# HCP Schemas
class HCPBase(BaseModel):
    full_name: str
    specialty: str
    organization: str
    email: Optional[str] = None

class HCPCreate(HCPBase):
    pass

class HCPResponse(HCPBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Interaction Schemas
class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str  # "In-Person", "Virtual", "Email", "Phone"
    interaction_date: date
    interaction_time: Optional[time] = None
    attendees: Optional[List[str]] = Field(default_factory=list)
    topics_discussed: Optional[List[str]] = Field(default_factory=list)
    materials_shared: Optional[List[str]] = Field(default_factory=list)
    samples_distributed: Optional[List[dict]] = Field(default_factory=list)  # e.g., [{"product": "Product A", "quantity": 5}]
    sentiment: str = "Neutral"  # "Positive", "Neutral", "Negative"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    follow_up_date: Optional[date] = None
    original_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    created_by: str = "System Rep"
    status: str = "Draft"  # "Draft", "Submitted"

    @field_validator("attendees", "topics_discussed", "materials_shared", mode="before")
    @classmethod
    def parse_json_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v or []

    @field_validator("samples_distributed", mode="before")
    @classmethod
    def parse_json_dict_list(cls, v: Any) -> List[dict]:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return []
        return v or []

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    hcp_id: Optional[int] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    attendees: Optional[List[str]] = None
    topics_discussed: Optional[List[str]] = None
    materials_shared: Optional[List[str]] = None
    samples_distributed: Optional[List[dict]] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    follow_up_date: Optional[date] = None
    original_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    created_by: Optional[str] = None
    status: Optional[str] = None

    @field_validator("attendees", "topics_discussed", "materials_shared", mode="before")
    @classmethod
    def parse_json_list(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("samples_distributed", mode="before")
    @classmethod
    def parse_json_dict_list(cls, v: Any) -> Optional[List[dict]]:
        if v is None:
            return None
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return []
        return v

class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    hcp: HCPResponse

    class Config:
        from_attributes = True

class InteractionTimelineItem(BaseModel):
    id: int
    interaction_type: str
    interaction_date: date
    topics_discussed: List[str]
    sentiment: str
    ai_summary: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime

    @field_validator("topics_discussed", mode="before")
    @classmethod
    def parse_json_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v or []

    class Config:
        from_attributes = True

class InteractionAuditResponse(BaseModel):
    id: int
    interaction_id: int
    action: str
    changed_fields: Optional[List[str]] = Field(default_factory=list)
    previous_values: Optional[dict] = Field(default_factory=dict)
    new_values: Optional[dict] = Field(default_factory=dict)
    timestamp: datetime

    @field_validator("changed_fields", mode="before")
    @classmethod
    def parse_changed_fields(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                pass
        return v or []

    @field_validator("previous_values", "new_values", mode="before")
    @classmethod
    def parse_json_dict(cls, v: Any) -> dict:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                pass
        return v or {}

    class Config:
        from_attributes = True


# Agent API Schemas
class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    current_state: Optional[dict] = {}

class AgentChatResponse(BaseModel):
    reply: str
    extracted_data: Optional[dict] = {}
    confidence: Optional[dict] = {}
    missing_fields: Optional[List[str]] = []
    status: str  # "active", "completed", "requires_confirmation"

class AgentExtractRequest(BaseModel):
    text: str

class AgentExtractResponse(BaseModel):
    extracted_data: dict
    compliance_warnings: List[str]

class AgentFollowUpRequest(BaseModel):
    interaction_id: Optional[int] = None
    notes: Optional[str] = None
    sentiment: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    outcomes: Optional[str] = None

class AgentFollowUpResponse(BaseModel):
    suggestions: List[str]
    recommended_date: Optional[date] = None
    is_ai_generated: bool = True
