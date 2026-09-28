import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Concept Schemas
class ConceptBase(BaseModel):
    id: str
    name: str
    description: str
    subject: str = "Basic Algebra"
    level: int = 1

    class Config:
        from_attributes = True

class ConceptWithPrereqs(ConceptBase):
    prerequisite_ids: List[str] = []

    class Config:
        from_attributes = True

class ConceptGraphNode(BaseModel):
    id: str
    name: str
    description: str
    level: int
    prerequisites: List[str]
    mastery_score: float = 0.0
    evidence_count: int = 0
    decay_applied: bool = False
    status: str = "locked"  # locked, ready, in_progress, mastered, needs_review

class ConceptGraphEdge(BaseModel):
    source: str
    target: str

class ConceptGraphResponse(BaseModel):
    nodes: List[ConceptGraphNode]
    edges: List[ConceptGraphEdge]
    learner_id: Optional[str] = None

# Learner Schemas
class LearnerBase(BaseModel):
    name: str

class LearnerCreate(LearnerBase):
    id: Optional[str] = None

class LearnerResponse(LearnerBase):
    id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Attempt Schemas
class AttemptCreate(BaseModel):
    learner_id: str
    concept_id: str
    correct: bool
    confidence: int = Field(ge=1, le=5, description="Self-reported confidence from 1 to 5")
    response_time_ms: int = Field(ge=0, description="Response time in milliseconds")
    hint_used: bool = False
    difficulty: str = Field(default="medium", description="easy, medium, or hard")

class AttemptResponse(BaseModel):
    id: int
    learner_id: str
    concept_id: str
    correct: bool
    confidence: int
    response_time_ms: int
    hint_used: bool
    difficulty: str
    timestamp: datetime.datetime
    is_rapid_guess: bool
    evidence_weight: float

    class Config:
        from_attributes = True

# Mastery State Schemas
class MasteryFactorBreakdown(BaseModel):
    prior_mastery: float
    posterior_mastery: float
    delta: float
    correctness_factor: float
    confidence_factor: float
    response_time_factor: float
    hint_penalty: float
    difficulty_weight: float
    anti_gaming_applied: bool
    decay_applied: bool
    explanation: str

class MasteryStateResponse(BaseModel):
    learner_id: str
    concept_id: str
    concept_name: Optional[str] = None
    mastery_score: float
    last_updated: datetime.datetime
    evidence_count: int
    decay_applied: bool
    raw_mastery_before_decay: Optional[float] = None
    factor_breakdown: Optional[MasteryFactorBreakdown] = None

    class Config:
        from_attributes = True

# Action Decision Schemas
class NextActionResponse(BaseModel):
    learner_id: str
    concept_id: str
    concept_name: str
    action: str  # Advance, Practice, Review, RemediatePrerequisite, Challenge, TeacherIntervention
    reason_text: str
    timestamp: datetime.datetime
    was_teacher_override: bool
    metrics: Dict[str, Any] = {}

class ActionLogResponse(BaseModel):
    id: int
    learner_id: str
    concept_id: str
    concept_name: Optional[str] = None
    action: str
    reason_text: str
    timestamp: datetime.datetime
    was_teacher_override: bool
    teacher_notes: Optional[str] = None

    class Config:
        from_attributes = True

class TeacherOverrideRequest(BaseModel):
    learner_id: str
    concept_id: str
    action: str  # Advance, Practice, Review, RemediatePrerequisite, Challenge, TeacherIntervention
    teacher_notes: Optional[str] = None

# Diagnostic Schemas
class DiagnosticQuestionResponse(BaseModel):
    id: str
    concept_id: str
    concept_name: str
    prompt: str
    options: List[str]
    difficulty: str
    hint_text: Optional[str] = None

class DiagnosticSubmissionItem(BaseModel):
    question_id: str
    selected_option: str
    confidence: int = 3
    response_time_ms: int = 15000
    hint_used: bool = False

class DiagnosticSubmitRequest(BaseModel):
    learner_name: str
    responses: List[DiagnosticSubmissionItem]

class DiagnosticResultResponse(BaseModel):
    learner_id: str
    learner_name: str
    total_questions: int
    correct_count: int
    diagnostic_score: float
    initial_mastery_states: List[MasteryStateResponse]
    recommended_start_concept: str
    recommended_action: NextActionResponse

# Teacher Dashboard Schemas
class HeatmapCell(BaseModel):
    concept_id: str
    concept_name: str
    mastery_score: float
    evidence_count: int
    status: str
    decay_applied: bool

class LearnerDashboardRow(BaseModel):
    learner_id: str
    learner_name: str
    created_at: datetime.datetime
    average_mastery: float
    mastery_cells: List[HeatmapCell]
    current_action: Optional[ActionLogResponse] = None
    is_stuck: bool = False
    stuck_reason: Optional[str] = None

class TeacherDashboardResponse(BaseModel):
    learners: List[LearnerDashboardRow]
    concepts: List[ConceptBase]
    stuck_learner_ids: List[str]
    recent_actions: List[ActionLogResponse]

# Simulation Comparison Schema
class LearnerComparisonCard(BaseModel):
    learner_id: str
    learner_name: str
    target_concept_id: str
    target_concept_name: str
    mastery_score: float
    evidence_count: int
    recent_attempts_summary: Dict[str, Any]
    next_action: str
    reason_text: str
    bkt_factors: Dict[str, Any]

class SimulationComparisonResponse(BaseModel):
    concept_id: str
    concept_name: str
    learner_a: LearnerComparisonCard
    learner_b: LearnerComparisonCard
    key_takeaway: str
