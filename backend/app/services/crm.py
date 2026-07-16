import json
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.crm import HCP, Interaction, InteractionAudit
from app.schemas.crm import HCPCreate, InteractionCreate, InteractionUpdate
from datetime import datetime

# HCP Services
def create_hcp(db: Session, hcp_in: HCPCreate) -> HCP:
    db_hcp = HCP(
        full_name=hcp_in.full_name,
        specialty=hcp_in.specialty,
        organization=hcp_in.organization,
        email=hcp_in.email
    )
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp

def get_hcp(db: Session, hcp_id: int) -> HCP:
    return db.query(HCP).filter(HCP.id == hcp_id).first()

def get_hcps(db: Session, skip: int = 0, limit: int = 100):
    return db.query(HCP).offset(skip).limit(limit).all()


# Interaction Services
def create_interaction(db: Session, interaction_in: InteractionCreate) -> Interaction:
    db_interaction = Interaction(
        hcp_id=interaction_in.hcp_id,
        interaction_type=interaction_in.interaction_type,
        interaction_date=interaction_in.interaction_date,
        interaction_time=interaction_in.interaction_time,
        attendees=json.dumps(interaction_in.attendees),
        topics_discussed=json.dumps(interaction_in.topics_discussed),
        materials_shared=json.dumps(interaction_in.materials_shared),
        samples_distributed=json.dumps(interaction_in.samples_distributed),
        sentiment=interaction_in.sentiment,
        outcomes=interaction_in.outcomes,
        follow_up_actions=interaction_in.follow_up_actions,
        follow_up_date=interaction_in.follow_up_date,
        original_notes=interaction_in.original_notes,
        ai_summary=interaction_in.ai_summary,
        created_by=interaction_in.created_by,
        status=interaction_in.status
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    
    # Audit log
    audit = InteractionAudit(
        interaction_id=db_interaction.id,
        action="CREATE",
        new_values=json.dumps(interaction_in.model_dump(mode="json"))
    )
    db.add(audit)
    db.commit()
    
    return db_interaction

def get_interaction(db: Session, interaction_id: int) -> Interaction:
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()

def get_interactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Interaction).order_by(desc(Interaction.interaction_date)).offset(skip).limit(limit).all()

def get_hcp_interactions(db: Session, hcp_id: int, limit: int = 10):
    return db.query(Interaction).filter(Interaction.hcp_id == hcp_id).order_by(desc(Interaction.interaction_date)).limit(limit).all()

def update_interaction(db: Session, interaction_id: int, updates: InteractionUpdate) -> Interaction:
    db_interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_interaction:
        return None
    
    previous_values = {}
    new_values = {}
    changed_fields = []
    
    update_data = updates.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        old_val = getattr(db_interaction, field)
        
        if field in ["attendees", "topics_discussed", "materials_shared", "samples_distributed"]:
            db_val = json.dumps(value)
            try:
                old_parsed = json.loads(old_val) if old_val else []
            except:
                old_parsed = old_val
                
            if old_parsed != value:
                previous_values[field] = old_parsed
                new_values[field] = value
                changed_fields.append(field)
                setattr(db_interaction, field, db_val)
        else:
            if old_val != value:
                previous_values[field] = str(old_val) if old_val is not None else None
                new_values[field] = str(value) if value is not None else None
                changed_fields.append(field)
                setattr(db_interaction, field, value)
                
    if changed_fields:
        db_interaction.updated_at = datetime.utcnow()
        db.add(db_interaction)
        
        audit = InteractionAudit(
            interaction_id=interaction_id,
            action="UPDATE",
            changed_fields=json.dumps(changed_fields),
            previous_values=json.dumps(previous_values),
            new_values=json.dumps(new_values)
        )
        db.add(audit)
        db.commit()
        db.refresh(db_interaction)
        
    return db_interaction
