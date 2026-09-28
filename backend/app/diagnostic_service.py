"""
MasteryFlow - Cold-Start Diagnostic Engine
==========================================
Provides diagnostic assessment covering root and intermediate concepts.
Derives initial Bayesian mastery priors P(L_0) from authentic diagnostic performance
instead of starting students at arbitrary 0% or static priors.
"""

import json
import uuid
import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .models import Learner, Concept, MasteryState, Attempt, DiagnosticQuestion
from .schemas import DiagnosticSubmissionItem, DiagnosticResultResponse, MasteryStateResponse, NextActionResponse
from .mastery_engine import calculate_bkt_update
from .decision_engine import evaluate_next_action
from .database import get_utc_now

# Static fallback questions to seed database if empty
DEFAULT_DIAGNOSTIC_BANK = [
    {
        "id": "diag_1",
        "concept_id": "c_arithmetic",
        "prompt": "Evaluate the order of operations: 48 ÷ (6 + 2) × 3",
        "options": ["18", "2", "8", "24"],
        "correct_answer": "18",
        "explanation": "Parentheses first: (6 + 2) = 8. Then left-to-right: 48 ÷ 8 = 6, and 6 × 3 = 18.",
        "difficulty": "easy",
        "hint_text": "Remember PEMDAS / BODMAS: perform parentheses first, then division and multiplication left to right."
    },
    {
        "id": "diag_2",
        "concept_id": "c_integers",
        "prompt": "Calculate: -14 - (-8) + (-6)",
        "options": ["-12", "-28", "0", "-4"],
        "correct_answer": "-12",
        "explanation": "-14 - (-8) becomes -14 + 8 = -6. Then -6 + (-6) = -12.",
        "difficulty": "easy",
        "hint_text": "Subtracting a negative is the same as adding a positive: -(-8) = +8."
    },
    {
        "id": "diag_3",
        "concept_id": "c_fractions",
        "prompt": "Add and simplify to lowest terms: 3/4 + 2/5",
        "options": ["23/20", "5/9", "1 1/4", "15/8"],
        "correct_answer": "23/20",
        "explanation": "Common denominator is 20: 3/4 = 15/20 and 2/5 = 8/20. 15/20 + 8/20 = 23/20 (or 1 3/20).",
        "difficulty": "medium",
        "hint_text": "Find a common denominator for 4 and 5 (which is 20) before adding the numerators."
    },
    {
        "id": "diag_4",
        "concept_id": "c_variables",
        "prompt": "If a = 3 and b = -2, evaluate the algebraic expression: 2a² - 4b",
        "options": ["26", "10", "22", "-10"],
        "correct_answer": "26",
        "explanation": "a² = 3² = 9. 2(9) = 18. -4b = -4(-2) = +8. 18 + 8 = 26.",
        "difficulty": "medium",
        "hint_text": "Square 3 first to get 9, then multiply by 2. Watch the negative signs when multiplying -4 by -2."
    },
    {
        "id": "diag_5",
        "concept_id": "c_ratios",
        "prompt": "A paint mix requires 3 parts blue to 5 parts yellow. To mix 40 liters total, how many liters of blue paint are needed?",
        "options": ["15 liters", "24 liters", "12 liters", "20 liters"],
        "correct_answer": "15 liters",
        "explanation": "Total parts = 3 + 5 = 8 parts. Each part = 40 ÷ 8 = 5 liters. Blue = 3 parts × 5 = 15 liters.",
        "difficulty": "medium",
        "hint_text": "Find the total number of parts in the ratio first, then determine the value of one part."
    },
    {
        "id": "diag_6",
        "concept_id": "c_one_step_eq",
        "prompt": "Solve for x: -7x = 63",
        "options": ["x = -9", "x = 9", "x = -70", "x = 56"],
        "correct_answer": "x = -9",
        "explanation": "Divide both sides by -7: x = 63 / -7 = -9.",
        "difficulty": "medium",
        "hint_text": "Isolate x by dividing both sides of the equation by the coefficient -7."
    }
]


def seed_diagnostic_questions_if_needed(db: Session):
    """Ensures diagnostic questions are present in database."""
    count = db.query(DiagnosticQuestion).count()
    if count == 0:
        for q in DEFAULT_DIAGNOSTIC_BANK:
            item = DiagnosticQuestion(
                id=q["id"],
                concept_id=q["concept_id"],
                prompt=q["prompt"],
                options_json=json.dumps(q["options"]),
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                difficulty=q["difficulty"],
                hint_text=q["hint_text"],
            )
            db.add(item)
        db.commit()


def get_diagnostic_questions(db: Session) -> List[Dict[str, Any]]:
    """Returns the list of diagnostic questions formatted for the frontend."""
    seed_diagnostic_questions_if_needed(db)
    questions = db.query(DiagnosticQuestion).all()
    results = []
    for q in questions:
        concept = db.query(Concept).filter(Concept.id == q.concept_id).first()
        results.append({
            "id": q.id,
            "concept_id": q.concept_id,
            "concept_name": concept.name if concept else q.concept_id,
            "prompt": q.prompt,
            "options": json.loads(q.options_json),
            "difficulty": q.difficulty,
            "hint_text": q.hint_text,
        })
    return results


def process_diagnostic_submission(
    db: Session,
    learner_name: str,
    responses: List[DiagnosticSubmissionItem]
) -> Dict[str, Any]:
    """
    Evaluates cold-start diagnostic:
    1. Creates new Learner.
    2. Scores each question.
    3. Derives initial mastery P(L_0) for tested concepts and propagates priors across DAG.
    4. Computes initial recommended next action.
    """
    now = get_utc_now()
    learner_id = f"learner_{uuid.uuid4().hex[:8]}"

    learner = Learner(id=learner_id, name=learner_name, created_at=now)
    db.add(learner)
    db.flush()

    # Load questions lookup
    questions = {q.id: q for q in db.query(DiagnosticQuestion).all()}
    
    concept_results: Dict[str, List[Dict[str, Any]]] = {}
    correct_count = 0

    for resp in responses:
        q = questions.get(resp.question_id)
        if not q:
            continue

        is_correct = (resp.selected_option.strip() == q.correct_answer.strip())
        if is_correct:
            correct_count += 1

        # Record attempt
        attempt = Attempt(
            learner_id=learner_id,
            concept_id=q.concept_id,
            correct=is_correct,
            confidence=resp.confidence,
            response_time_ms=resp.response_time_ms,
            hint_used=resp.hint_used,
            difficulty=q.difficulty,
            timestamp=now,
            is_rapid_guess=False,
            evidence_weight=1.0,
        )
        db.add(attempt)

        if q.concept_id not in concept_results:
            concept_results[q.concept_id] = []
        concept_results[q.concept_id].append({
            "correct": is_correct,
            "confidence": resp.confidence,
            "hint_used": resp.hint_used,
            "difficulty": q.difficulty,
            "response_time_ms": resp.response_time_ms
        })

    db.flush()

    # Calculate initial mastery states
    all_concepts = db.query(Concept).all()
    concept_map = {c.id: c for c in all_concepts}
    mastery_map: Dict[str, float] = {}

    for concept_id, attempts_list in concept_results.items():
        # Derive initial belief from diagnostic evidence
        # Cold root prior base: 0.15
        current_p = 0.15
        for att in attempts_list:
            bkt = calculate_bkt_update(
                prior_mastery=current_p,
                correct=att["correct"],
                confidence=att["confidence"],
                response_time_ms=att["response_time_ms"],
                hint_used=att["hint_used"],
                difficulty=att["difficulty"]
            )
            current_p = bkt["posterior_mastery"]

        mastery_map[concept_id] = current_p

    # Propagate priors to untested concepts based on prerequisite parents
    for concept in all_concepts:
        if concept.id not in mastery_map:
            if not concept.prerequisites:
                # Untested root concept: neutral cold prior
                derived_prior = 0.15
            else:
                # Dependent concept: prior influenced by prerequisites
                prereq_scores = [
                    mastery_map.get(p.id, 0.15) for p in concept.prerequisites
                ]
                avg_prereq = sum(prereq_scores) / len(prereq_scores)
                # If prerequisites are high, downstream concept has higher readiness prior
                derived_prior = round(max(0.10, min(0.40, avg_prereq * 0.45)), 3)

            mastery_map[concept.id] = derived_prior

    # Save MasteryState objects
    saved_states = []
    for c_id, score in mastery_map.items():
        evidence_n = len(concept_results.get(c_id, []))
        state = MasteryState(
            learner_id=learner_id,
            concept_id=c_id,
            mastery_score=score,
            raw_mastery_before_decay=score,
            evidence_count=evidence_n,
            last_updated=now,
            decay_applied=False,
        )
        db.add(state)
        saved_states.append({
            "learner_id": learner_id,
            "concept_id": c_id,
            "concept_name": concept_map[c_id].name if c_id in concept_map else c_id,
            "mastery_score": score,
            "last_updated": now,
            "evidence_count": evidence_n,
            "decay_applied": False,
        })

    db.commit()

    # Determine first next action
    first_action = evaluate_next_action(db, learner_id)

    total_q = len(responses)
    score_pct = round((correct_count / total_q) * 100, 1) if total_q > 0 else 0.0

    return {
        "learner_id": learner_id,
        "learner_name": learner_name,
        "total_questions": total_q,
        "correct_count": correct_count,
        "diagnostic_score": score_pct,
        "initial_mastery_states": saved_states,
        "recommended_start_concept": first_action["concept_name"],
        "recommended_action": first_action,
    }
