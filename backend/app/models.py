import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from .database import Base, get_utc_now

# Many-to-many relationship table for concept prerequisites (DAG structure)
concept_prerequisites = Table(
    "concept_prerequisites",
    Base.metadata,
    Column("concept_id", String, ForeignKey("concepts.id"), primary_key=True),
    Column("prerequisite_id", String, ForeignKey("concepts.id"), primary_key=True),
)

class Concept(Base):
    """
    Concept representation in the knowledge graph.
    Forms a Directed Acyclic Graph (DAG) via prerequisites.
    """
    __tablename__ = "concepts"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    subject = Column(String, default="Basic Algebra")
    level = Column(Integer, default=1)  # Depth level in the DAG for topological rendering

    # Direct prerequisites for this concept
    prerequisites = relationship(
        "Concept",
        secondary=concept_prerequisites,
        primaryjoin=id == concept_prerequisites.c.concept_id,
        secondaryjoin=id == concept_prerequisites.c.prerequisite_id,
        backref="dependent_concepts",
    )

    # Relationships
    attempts = relationship("Attempt", back_populates="concept", cascade="all, delete-orphan")
    mastery_states = relationship("MasteryState", back_populates="concept", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="concept", cascade="all, delete-orphan")
    questions = relationship("DiagnosticQuestion", back_populates="concept", cascade="all, delete-orphan")


class Learner(Base):
    """
    Student / learner entity profile.
    """
    __tablename__ = "learners"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    # Relationships
    attempts = relationship("Attempt", back_populates="learner", cascade="all, delete-orphan")
    mastery_states = relationship("MasteryState", back_populates="learner", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="learner", cascade="all, delete-orphan")


class Attempt(Base):
    """
    Individual learning attempt / question response with rich cognitive & behavioral metrics.
    """
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    learner_id = Column(String, ForeignKey("learners.id"), nullable=False, index=True)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False, index=True)
    correct = Column(Boolean, nullable=False)
    confidence = Column(Integer, nullable=False)  # Self-reported 1 to 5
    response_time_ms = Column(Integer, nullable=False)  # Time in milliseconds
    hint_used = Column(Boolean, default=False, nullable=False)
    difficulty = Column(String, default="medium", nullable=False)  # easy, medium, hard
    timestamp = Column(DateTime, default=get_utc_now, nullable=False)

    # Anti-gaming metadata
    is_rapid_guess = Column(Boolean, default=False)
    evidence_weight = Column(Float, default=1.0)  # Effective weighting after anti-gaming discounts

    # Relationships
    learner = relationship("Learner", back_populates="attempts")
    concept = relationship("Concept", back_populates="attempts")


class MasteryState(Base):
    """
    Current Bayesian/heuristic mastery belief for a given (learner, concept) pair.
    """
    __tablename__ = "mastery_states"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    learner_id = Column(String, ForeignKey("learners.id"), nullable=False, index=True)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False, index=True)
    mastery_score = Column(Float, default=0.0, nullable=False)  # Range: [0.0, 1.0]
    last_updated = Column(DateTime, default=get_utc_now, nullable=False)
    evidence_count = Column(Integer, default=0, nullable=False)
    decay_applied = Column(Boolean, default=False, nullable=False)
    raw_mastery_before_decay = Column(Float, nullable=True)

    # Relationships
    learner = relationship("Learner", back_populates="mastery_states")
    concept = relationship("Concept", back_populates="mastery_states")


class ActionLog(Base):
    """
    Audit log of system or teacher recommended next actions with full explainability.
    """
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    learner_id = Column(String, ForeignKey("learners.id"), nullable=False, index=True)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # Advance, Practice, Review, RemediatePrerequisite, Challenge, TeacherIntervention
    reason_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=get_utc_now, nullable=False)
    was_teacher_override = Column(Boolean, default=False, nullable=False)
    teacher_notes = Column(Text, nullable=True)

    # Relationships
    learner = relationship("Learner", back_populates="action_logs")
    concept = relationship("Concept", back_populates="action_logs")


class DiagnosticQuestion(Base):
    """
    Diagnostic & practice question bank for cold start and live attempts.
    """
    __tablename__ = "diagnostic_questions"

    id = Column(String, primary_key=True, index=True)
    concept_id = Column(String, ForeignKey("concepts.id"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON array of strings
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    difficulty = Column(String, default="medium")  # easy, medium, hard
    hint_text = Column(Text, nullable=True)

    # Relationships
    concept = relationship("Concept", back_populates="questions")
