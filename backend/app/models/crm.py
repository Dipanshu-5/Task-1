from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class HCP(Base):
    __tablename__ = "hcps"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # "In-Person", "Virtual", "Email", "Phone"
    interaction_date = Column(Date, nullable=False)
    interaction_time = Column(Time, nullable=True)
    attendees = Column(Text, nullable=True)  # JSON-serialized list
    topics_discussed = Column(Text, nullable=True)  # JSON-serialized list
    materials_shared = Column(Text, nullable=True)  # JSON-serialized list
    samples_distributed = Column(Text, nullable=True)  # JSON-serialized list
    sentiment = Column(String(50), nullable=False, default="Neutral")  # "Positive", "Neutral", "Negative"
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    original_notes = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False, default="System Rep")
    status = Column(String(50), nullable=False, default="Draft")  # "Draft", "Submitted"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    hcp = relationship("HCP", back_populates="interactions")
    audits = relationship("InteractionAudit", back_populates="interaction", cascade="all, delete-orphan")


class InteractionAudit(Base):
    __tablename__ = "interaction_audits"
    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id"), nullable=False)
    action = Column(String(50), nullable=False)  # "CREATE", "UPDATE", "DELETE"
    changed_fields = Column(Text, nullable=True)  # JSON-serialized list of field names
    previous_values = Column(Text, nullable=True)  # JSON-serialized dict
    new_values = Column(Text, nullable=True)  # JSON-serialized dict
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    interaction = relationship("Interaction", back_populates="audits")
