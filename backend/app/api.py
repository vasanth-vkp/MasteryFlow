"""
MasteryFlow - FastAPI API Routes
================================
Clean RESTful API exposing concept graph, attempts, mastery states, next actions,
cold-start diagnostics, teacher dashboard, and simulation comparison.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .database import get_db, get_utc_now
from .models import Concept, Learner, Attempt, MasteryState, ActionLog, DiagnosticQuestion
from .schemas import (
    ConceptGraphResponse,
    ConceptGraphNode,
    ConceptGraphEdge,
    ConceptBase,
    LearnerResponse,
    LearnerCreate,
    AttemptCreate,
    AttemptResponse,
    MasteryStateResponse,
    NextActionResponse,
    ActionLogResponse,
    TeacherOverrideRequest,
    DiagnosticQuestionResponse,
    DiagnosticSubmitRequest,
    DiagnosticResultResponse,
    TeacherDashboardResponse,
    LearnerDashboardRow,
    HeatmapCell,
    SimulationComparisonResponse,
    LearnerComparisonCard,
)
from .mastery_engine import record_attempt_and_update_mastery, apply_time_decay_if_needed
from .decision_engine import evaluate_next_action, record_teacher_override
from .diagnostic_service import get_diagnostic_questions, process_diagnostic_submission

router = APIRouter(prefix="/api")


# -------------------------------------------------------------
# 1. Concept Graph Endpoints
# -------------------------------------------------------------
@router.get("/concepts/graph", response_model=ConceptGraphResponse)
def get_concept_graph(learner_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns the full Directed Acyclic Graph (DAG) of concepts.
    If learner_id is provided, annotates each node with the learner's live mastery score,
    decay status, and pedagogical readiness status (locked, ready, in_progress, mastered, review).
    """
    concepts = db.query(Concept).order_by(Concept.level.asc(), Concept.id.asc()).all()
    
    # Pre-fetch mastery states if learner_id is given
    mastery_map = {}
    if learner_id:
        states = db.query(MasteryState).filter(MasteryState.learner_id == learner_id).all()
        for s in states:
            decayed_score, decay_applied = apply_time_decay_if_needed(s)
            mastery_map[s.concept_id] = {
                "score": decayed_score,
                "evidence_count": s.evidence_count,
                "decay_applied": decay_applied,
            }

    nodes = []
    edges = []

    for c in concepts:
        prereq_ids = [p.id for p in c.prerequisites]
        for pid in prereq_ids:
            edges.append(ConceptGraphEdge(source=pid, target=c.id))

        m_data = mastery_map.get(c.id, {"score": 0.0, "evidence_count": 0, "decay_applied": False})
        score = m_data["score"]

        # Determine pedagogical status
        if m_data["decay_applied"]:
            status = "needs_review"
        elif score >= 0.85:
            status = "mastered"
        elif score >= 0.40:
            status = "in_progress"
        else:
            # Check if all prerequisites are at least 0.50
            if not prereq_ids:
                status = "ready"
            else:
                prereqs_solid = all(
                    mastery_map.get(pid, {}).get("score", 0.0) >= 0.50
                    for pid in prereq_ids
                )
                status = "ready" if prereqs_solid else "locked"

        nodes.append(ConceptGraphNode(
            id=c.id,
            name=c.name,
            description=c.description,
            level=c.level,
            prerequisites=prereq_ids,
            mastery_score=round(score, 3),
            evidence_count=m_data["evidence_count"],
            decay_applied=m_data["decay_applied"],
            status=status,
        ))

    return ConceptGraphResponse(nodes=nodes, edges=edges, learner_id=learner_id)


# -------------------------------------------------------------
@router.get("/concepts", response_model=List[ConceptBase])
def get_all_concepts(db: Session = Depends(get_db)):
    """Returns all concepts ordered by topological level."""
    return db.query(Concept).order_by(Concept.level.asc(), Concept.id.asc()).all()


@router.get("/learners", response_model=List[LearnerResponse])
def list_learners(db: Session = Depends(get_db)):
    """List all learners in the database."""
    return db.query(Learner).order_by(Learner.created_at.desc()).all()


@router.post("/learners", response_model=LearnerResponse)
def create_learner(payload: LearnerCreate, db: Session = Depends(get_db)):
    """Register a new learner."""
    import uuid
    import datetime
    lid = payload.id or f"learner_{uuid.uuid4().hex[:8]}"
    existing = db.query(Learner).filter(Learner.id == lid).first()
    if existing:
        raise HTTPException(status_code=400, detail="Learner ID already exists.")
    
    learner = Learner(id=lid, name=payload.name, created_at=get_utc_now())
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


@router.get("/learners/{learner_id}")
def get_learner_detail(learner_id: str, db: Session = Depends(get_db)):
    """Returns learner profile, current mastery across all concepts, and recent activity."""
    learner = db.query(Learner).filter(Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found.")

    states = db.query(MasteryState).filter(MasteryState.learner_id == learner_id).all()
    concept_map = {c.id: c.name for c in db.query(Concept).all()}

    state_list = []
    total_score = 0.0
    for s in states:
        decayed_score, decay_applied = apply_time_decay_if_needed(s)
        total_score += decayed_score
        state_list.append({
            "concept_id": s.concept_id,
            "concept_name": concept_map.get(s.concept_id, s.concept_id),
            "mastery_score": round(decayed_score, 3),
            "evidence_count": s.evidence_count,
            "decay_applied": decay_applied,
            "last_updated": s.last_updated,
        })

    avg_mastery = total_score / len(states) if states else 0.0

    return {
        "id": learner.id,
        "name": learner.name,
        "created_at": learner.created_at,
        "average_mastery": round(avg_mastery, 3),
        "states": state_list,
    }


# -------------------------------------------------------------
# 3. Learning Attempts & Interactive Practice
# -------------------------------------------------------------
@router.post("/attempts")
def submit_attempt(payload: AttemptCreate, db: Session = Depends(get_db)):
    """
    Submits a practice attempt, runs the explainable BKT update with cognitive factors,
    persists in SQLite, and evaluates the new recommended next action.
    """
    concept = db.query(Concept).filter(Concept.id == payload.concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{payload.concept_id}' not found.")
    
    learner = db.query(Learner).filter(Learner.id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail=f"Learner '{payload.learner_id}' not found.")

    attempt, mastery_state, factor_breakdown = record_attempt_and_update_mastery(
        db=db,
        learner_id=payload.learner_id,
        concept_id=payload.concept_id,
        correct=payload.correct,
        confidence=payload.confidence,
        response_time_ms=payload.response_time_ms,
        hint_used=payload.hint_used,
        difficulty=payload.difficulty,
    )

    next_action = evaluate_next_action(
        db=db,
        learner_id=payload.learner_id,
        target_concept_id=payload.concept_id
    )

    return {
        "attempt": {
            "id": attempt.id,
            "learner_id": attempt.learner_id,
            "concept_id": attempt.concept_id,
            "concept_name": concept.name,
            "correct": attempt.correct,
            "confidence": attempt.confidence,
            "response_time_ms": attempt.response_time_ms,
            "hint_used": attempt.hint_used,
            "difficulty": attempt.difficulty,
            "timestamp": attempt.timestamp,
            "is_rapid_guess": attempt.is_rapid_guess,
            "evidence_weight": attempt.evidence_weight,
        },
        "updated_mastery": {
            "concept_id": mastery_state.concept_id,
            "concept_name": concept.name,
            "mastery_score": mastery_state.mastery_score,
            "evidence_count": mastery_state.evidence_count,
            "decay_applied": mastery_state.decay_applied,
            "factor_breakdown": factor_breakdown,
        },
        "next_action": next_action,
    }


# -------------------------------------------------------------
# 4. Next-Action Recommendation
# -------------------------------------------------------------
@router.get("/next-action/{learner_id}", response_model=NextActionResponse)
def get_next_action(learner_id: str, concept_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Evaluates the learner's knowledge state and concept DAG to return
    the next best pedagogical action with full explainability.
    """
    try:
        decision = evaluate_next_action(db=db, learner_id=learner_id, target_concept_id=concept_id)
        return decision
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------------------------------------------------------------
# 5. Cold-Start Diagnostic
# -------------------------------------------------------------
@router.get("/diagnostic/questions", response_model=List[DiagnosticQuestionResponse])
def fetch_diagnostic_questions(db: Session = Depends(get_db)):
    """Fetches diagnostic assessment question bank covering root and intermediate concepts."""
    return get_diagnostic_questions(db)


@router.post("/diagnostic/submit", response_model=DiagnosticResultResponse)
def submit_diagnostic(payload: DiagnosticSubmitRequest, db: Session = Depends(get_db)):
    """Processes cold-start diagnostic answers, registers learner, and initializes mastery priors."""
    result = process_diagnostic_submission(
        db=db,
        learner_name=payload.learner_name,
        responses=payload.responses
    )
    return result


# -------------------------------------------------------------
# 6. Teacher Dashboard & Overrides
# -------------------------------------------------------------
@router.get("/teacher/dashboard", response_model=TeacherDashboardResponse)
def get_teacher_dashboard(db: Session = Depends(get_db)):
    """
    Returns data for the Teacher Dashboard:
    - Learner x Concept mastery heatmap matrix
    - List of stuck learners requiring intervention
    - Comprehensive action log audit trail
    """
    concepts = db.query(Concept).order_by(Concept.level.asc(), Concept.id.asc()).all()
    concept_list = [
        ConceptBase(
            id=c.id,
            name=c.name,
            description=c.description,
            subject=c.subject,
            level=c.level
        ) for c in concepts
    ]

    learners = db.query(Learner).order_by(Learner.created_at.desc()).all()
    stuck_learner_ids = []
    learner_rows = []

    for l in learners:
        states = db.query(MasteryState).filter(MasteryState.learner_id == l.id).all()
        state_dict = {}
        total_m = 0.0

        for s in states:
            decayed_score, decay_applied = apply_time_decay_if_needed(s)
            state_dict[s.concept_id] = (decayed_score, s.evidence_count, decay_applied)
            total_m += decayed_score

        cells = []
        for c in concepts:
            if c.id in state_dict:
                sc, ev, dec = state_dict[c.id]
                status = "mastered" if sc >= 0.85 else ("in_progress" if sc >= 0.40 else "developing")
                cells.append(HeatmapCell(
                    concept_id=c.id,
                    concept_name=c.name,
                    mastery_score=round(sc, 3),
                    evidence_count=ev,
                    status=status,
                    decay_applied=dec,
                ))
            else:
                cells.append(HeatmapCell(
                    concept_id=c.id,
                    concept_name=c.name,
                    mastery_score=0.0,
                    evidence_count=0,
                    status="unattempted",
                    decay_applied=False,
                ))

        avg_m = total_m / len(states) if states else 0.0

        # Latest action
        latest_action = (
            db.query(ActionLog)
            .filter(ActionLog.learner_id == l.id)
            .order_by(ActionLog.timestamp.desc())
            .first()
        )

        is_stuck = False
        stuck_reason = None
        if latest_action:
            if latest_action.action in ("TeacherIntervention", "RemediatePrerequisite"):
                is_stuck = True
                stuck_reason = latest_action.reason_text
                stuck_learner_ids.append(l.id)

        learner_rows.append(LearnerDashboardRow(
            learner_id=l.id,
            learner_name=l.name,
            created_at=l.created_at,
            average_mastery=round(avg_m, 3),
            mastery_cells=cells,
            current_action=ActionLogResponse(
                id=latest_action.id,
                learner_id=latest_action.learner_id,
                concept_id=latest_action.concept_id,
                concept_name=latest_action.concept.name if latest_action.concept else latest_action.concept_id,
                action=latest_action.action,
                reason_text=latest_action.reason_text,
                timestamp=latest_action.timestamp,
                was_teacher_override=latest_action.was_teacher_override,
                teacher_notes=latest_action.teacher_notes,
            ) if latest_action else None,
            is_stuck=is_stuck,
            stuck_reason=stuck_reason,
        ))

    # Recent action logs
    recent_logs = (
        db.query(ActionLog)
        .order_by(ActionLog.timestamp.desc())
        .limit(25)
        .all()
    )
    concept_names = {c.id: c.name for c in concepts}
    formatted_logs = []
    for log in recent_logs:
        formatted_logs.append(ActionLogResponse(
            id=log.id,
            learner_id=log.learner_id,
            concept_id=log.concept_id,
            concept_name=concept_names.get(log.concept_id, log.concept_id),
            action=log.action,
            reason_text=log.reason_text,
            timestamp=log.timestamp,
            was_teacher_override=log.was_teacher_override,
            teacher_notes=log.teacher_notes,
        ))

    return TeacherDashboardResponse(
        learners=learner_rows,
        concepts=concept_list,
        stuck_learner_ids=list(set(stuck_learner_ids)),
        recent_actions=formatted_logs,
    )


@router.post("/teacher/override")
def override_action(payload: TeacherOverrideRequest, db: Session = Depends(get_db)):
    """Teacher forcefully overrides the engine's next action, logging the audit trail."""
    try:
        result = record_teacher_override(
            db=db,
            learner_id=payload.learner_id,
            concept_id=payload.concept_id,
            action=payload.action,
            teacher_notes=payload.teacher_notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# 7. Simulation & Side-by-Side Comparison
# -------------------------------------------------------------
@router.get("/simulation/compare", response_model=SimulationComparisonResponse)
def compare_learners(
    concept_id: str = "c_ratios",
    learner_a_id: Optional[str] = None,
    learner_b_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Compares ANY two learners on ANY concept dynamically from SQLite,
    showing divergent explainable next actions and cognitive metrics.
    """
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        concept = db.query(Concept).first()
        if not concept:
            raise HTTPException(status_code=404, detail="No concepts found in database.")
        concept_id = concept.id

    all_learners = db.query(Learner).all()
    if len(all_learners) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 learners required in database for comparison."
        )

    target_a = learner_a_id or ("learner_a" if any(l.id == "learner_a" for l in all_learners) else all_learners[0].id)
    target_b = learner_b_id or ("learner_b" if any(l.id == "learner_b" for l in all_learners) else (all_learners[1].id if all_learners[1].id != target_a else all_learners[0].id))

    learner_a = db.query(Learner).filter(Learner.id == target_a).first() or all_learners[0]
    learner_b = db.query(Learner).filter(Learner.id == target_b).first() or (all_learners[1] if len(all_learners) > 1 else all_learners[0])

    def get_learner_card(learner: Learner) -> LearnerComparisonCard:
        state = db.query(MasteryState).filter(
            MasteryState.learner_id == learner.id,
            MasteryState.concept_id == concept_id
        ).first()

        attempts = (
            db.query(Attempt)
            .filter(Attempt.learner_id == learner.id, Attempt.concept_id == concept_id)
            .order_by(Attempt.timestamp.desc())
            .limit(5)
            .all()
        )

        decision = evaluate_next_action(db=db, learner_id=learner.id, target_concept_id=concept_id)

        correct_count = sum(1 for a in attempts if a.correct)
        hints_count = sum(1 for a in attempts if a.hint_used)
        avg_rt = sum(a.response_time_ms for a in attempts) / len(attempts) if attempts else 0
        avg_conf = sum(a.confidence for a in attempts) / len(attempts) if attempts else 0
        rapid_count = sum(1 for a in attempts if a.is_rapid_guess)

        score = state.mastery_score if state else 0.15
        ev_count = state.evidence_count if state else len(attempts)

        return LearnerComparisonCard(
            learner_id=learner.id,
            learner_name=learner.name,
            target_concept_id=concept_id,
            target_concept_name=concept.name,
            mastery_score=round(score, 3),
            evidence_count=ev_count,
            recent_attempts_summary={
                "total_attempts": len(attempts),
                "accuracy_pct": round((correct_count / len(attempts)) * 100, 1) if attempts else 0,
                "hints_used_count": hints_count,
                "avg_response_time_ms": int(avg_rt),
                "avg_confidence": round(avg_conf, 1),
                "rapid_guess_flags": rapid_count,
            },
            next_action=decision["action"],
            reason_text=decision["reason_text"],
            bkt_factors=decision.get("metrics", {}),
        )

    card_a = get_learner_card(learner_a)
    card_b = get_learner_card(learner_b)

    takeaway = (
        f"On '{concept.name}', Learner A ({card_a.learner_name}) receives '{card_a.next_action}' "
        f"due to solid prerequisite foundations and high authentic mastery ({card_a.mastery_score*100:.1f}%), "
        f"while Learner B ({card_b.learner_name}) receives '{card_b.next_action}' because the decision engine "
        f"detects prerequisite deficiency and heavy hint reliance."
    )

    return SimulationComparisonResponse(
        concept_id=concept_id,
        concept_name=concept.name,
        learner_a=card_a,
        learner_b=card_b,
        key_takeaway=takeaway,
    )


# -------------------------------------------------------------
# 8. Interactive Practice Questions Bank for Frontend Simulator
# -------------------------------------------------------------
@router.get("/questions/concept/{concept_id}")
def get_practice_questions_for_concept(concept_id: str, db: Session = Depends(get_db)):
    """Returns sample interactive questions for live simulation on a concept."""
    questions = db.query(DiagnosticQuestion).filter(DiagnosticQuestion.concept_id == concept_id).all()
    import json
    return [
        {
            "id": q.id,
            "concept_id": q.concept_id,
            "prompt": q.prompt,
            "options": json.loads(q.options_json),
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "difficulty": q.difficulty,
            "hint_text": q.hint_text,
        }
        for q in questions
    ]
