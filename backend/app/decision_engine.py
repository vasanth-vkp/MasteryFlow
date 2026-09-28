"""
MasteryFlow - Explainable Next-Action Decision & Intervention Engine
====================================================================
This module evaluates the learner's knowledge state, attempt history, and the
prerequisite Directed Acyclic Graph (DAG) to deterministically recommend the next
optimal pedagogical action with 100% inspectable, number-grounded explanations.

Possible Actions:
-----------------
1. TeacherIntervention: Triggered upon persistent struggle (e.g. 3+ consecutive failures,
   heavy hint dependency, low mastery) requiring human educator support.
2. RemediatePrerequisite: Triggered when target concept has any prerequisite with mastery < 0.50.
3. Review: Triggered by spaced repetition / Ebbinghaus memory decay (> 7 days inactive).
4. Practice: Target concept mastery is in developing zone (0.40 <= M < 0.85).
5. Challenge: Concept mastered (M >= 0.85) with high confidence & speed.
6. Advance: Concept mastered (M >= 0.85), prerequisites solid -> recommend next DAG concept.
"""

import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from .models import Concept, MasteryState, Attempt, ActionLog, Learner
from .mastery_engine import apply_time_decay_if_needed
from .database import get_utc_now

PREREQUISITE_MASTERY_THRESHOLD = 0.50
MASTERY_PROFICIENCY_THRESHOLD = 0.85
DEVELOPING_ZONE_LOWER = 0.40
MAX_CONSECUTIVE_FAILURES_BEFORE_INTERVENTION = 3


def get_or_create_mastery_state(db: Session, learner_id: str, concept_id: str) -> MasteryState:
    """Helper to fetch or init a MasteryState with baseline decay checked."""
    state = (
        db.query(MasteryState)
        .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == concept_id)
        .first()
    )
    if not state:
        state = MasteryState(
            learner_id=learner_id,
            concept_id=concept_id,
            mastery_score=0.15,
            raw_mastery_before_decay=0.15,
            evidence_count=0,
            last_updated=get_utc_now(),
            decay_applied=False,
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    else:
        # Check time decay dynamically
        decayed_score, decay_applied = apply_time_decay_if_needed(state)
        if decay_applied and not state.decay_applied:
            state.mastery_score = decayed_score
            state.decay_applied = True
            db.commit()
            db.refresh(state)

    return state


def evaluate_next_action(
    db: Session,
    learner_id: str,
    target_concept_id: Optional[str] = None,
    allow_teacher_override_check: bool = True
) -> Dict[str, Any]:
    """
    Core deterministic policy algorithm.
    Takes the learner model + concept graph, evaluates rules in strict pedagogical order,
    and returns the decision payload with human-readable numeric justification.
    """
    learner = db.query(Learner).filter(Learner.id == learner_id).first()
    if not learner:
        raise ValueError(f"Learner '{learner_id}' not found.")

    # If no target concept specified, pick current learning frontier in DAG
    if not target_concept_id:
        target_concept = select_frontier_concept(db, learner_id)
        target_concept_id = target_concept.id
    else:
        target_concept = db.query(Concept).filter(Concept.id == target_concept_id).first()
        if not target_concept:
            raise ValueError(f"Concept '{target_concept_id}' not found.")

    # 1. Check for recent unfulfilled Teacher Override on this concept
    if allow_teacher_override_check:
        latest_action = (
            db.query(ActionLog)
            .filter(ActionLog.learner_id == learner_id, ActionLog.concept_id == target_concept_id)
            .order_by(ActionLog.timestamp.desc())
            .first()
        )
        if latest_action and latest_action.was_teacher_override:
            # Check if learner has made attempts since the override
            attempts_since = (
                db.query(Attempt)
                .filter(
                    Attempt.learner_id == learner_id,
                    Attempt.concept_id == target_concept_id,
                    Attempt.timestamp > latest_action.timestamp
                )
                .count()
            )
            if attempts_since == 0:
                # Teacher override is active and pending execution
                return {
                    "learner_id": learner_id,
                    "concept_id": target_concept_id,
                    "concept_name": target_concept.name,
                    "action": latest_action.action,
                    "reason_text": f"[Teacher Override Active] {latest_action.reason_text} (Notes: {latest_action.teacher_notes or 'None'})",
                    "timestamp": latest_action.timestamp,
                    "was_teacher_override": True,
                    "metrics": {
                        "override_active": True,
                        "teacher_notes": latest_action.teacher_notes,
                    }
                }

    # Fetch target concept mastery state
    c_state = get_or_create_mastery_state(db, learner_id, target_concept_id)
    c_mastery = c_state.mastery_score

    # Fetch recent attempts on target concept
    recent_attempts = (
        db.query(Attempt)
        .filter(Attempt.learner_id == learner_id, Attempt.concept_id == target_concept_id)
        .order_by(Attempt.timestamp.desc())
        .limit(5)
        .all()
    )

    consecutive_failures = 0
    hints_in_last_three = 0
    for i, att in enumerate(recent_attempts[:3]):
        if not att.correct:
            consecutive_failures += 1
        if att.hint_used:
            hints_in_last_three += 1

    # -------------------------------------------------------------
    # RULE 1: Teacher Intervention (Repeated Failures / Struggle)
    # -------------------------------------------------------------
    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES_BEFORE_INTERVENTION or (
        consecutive_failures >= 2 and hints_in_last_three >= 2 and c_mastery < 0.40
    ):
        action = "TeacherIntervention"
        reason = (
            f"Struggle detected on {target_concept.name}: {consecutive_failures} consecutive failed attempts "
            f"({hints_in_last_three} of last 3 used hints). Mastery dropped to {c_mastery*100:.1f}%. "
            f"Escalating to Teacher Intervention for targeted instructional support."
        )
        return log_and_format_decision(db, learner_id, target_concept_id, target_concept.name, action, reason, False, {
            "mastery_score": c_mastery,
            "consecutive_failures": consecutive_failures,
            "hints_used": hints_in_last_three,
        })

    # -------------------------------------------------------------
    # RULE 2: Prerequisite Remediation (DAG Integrity Check)
    # -------------------------------------------------------------
    prereqs = target_concept.prerequisites
    weak_prereqs = []
    for p in prereqs:
        p_state = get_or_create_mastery_state(db, learner_id, p.id)
        if p_state.mastery_score < PREREQUISITE_MASTERY_THRESHOLD:
            weak_prereqs.append((p, p_state.mastery_score))

    if weak_prereqs:
        # Sort by lowest score first
        weak_prereqs.sort(key=lambda x: x[1])
        weakest_p, weakest_score = weak_prereqs[0]

        # Count hint attempts on that prereq
        p_hints = (
            db.query(Attempt)
            .filter(Attempt.learner_id == learner_id, Attempt.concept_id == weakest_p.id, Attempt.hint_used == True)
            .count()
        )
        p_recent = (
            db.query(Attempt)
            .filter(Attempt.learner_id == learner_id, Attempt.concept_id == weakest_p.id)
            .count()
        )

        action = "RemediatePrerequisite"
        reason = (
            f"Prerequisite barrier: Review '{weakest_p.name}' before practicing '{target_concept.name}'. "
            f"Prerequisite mastery is {weakest_score*100:.1f}% (< 50% threshold required). "
            f"Evidence: {p_hints} of {p_recent} prior attempts required hints."
        )
        return log_and_format_decision(db, learner_id, weakest_p.id, weakest_p.name, action, reason, False, {
            "target_concept_id": target_concept_id,
            "target_concept_name": target_concept.name,
            "blocking_prerequisite_id": weakest_p.id,
            "blocking_prerequisite_name": weakest_p.name,
            "prerequisite_mastery": weakest_score,
        })

    # -------------------------------------------------------------
    # RULE 3: Spaced Repetition Review (Decay Alert)
    # -------------------------------------------------------------
    if c_state.decay_applied:
        days_inactive = (get_utc_now() - c_state.last_updated).total_seconds() / 86400.0
        action = "Review"
        reason = (
            f"Spaced review triggered for '{target_concept.name}': Concept untouched for {max(7, int(days_inactive))} days. "
            f"Retention estimate decayed from {c_state.raw_mastery_before_decay*100:.1f}% to {c_mastery*100:.1f}%. "
            f"Complete a refresher set to restore full mastery confidence."
        )
        return log_and_format_decision(db, learner_id, target_concept_id, target_concept.name, action, reason, False, {
            "decay_applied": True,
            "current_mastery": c_mastery,
            "pre_decay_mastery": c_state.raw_mastery_before_decay,
        })

    # -------------------------------------------------------------
    # RULE 4: Practice (Developing Zone: 0.40 <= M < 0.85)
    # -------------------------------------------------------------
    if c_mastery < MASTERY_PROFICIENCY_THRESHOLD:
        action = "Practice"
        reason = (
            f"Target concept '{target_concept.name}' is developing at {c_mastery*100:.1f}% mastery "
            f"(target: >=85%). {c_state.evidence_count} evidence items recorded. Continue adaptive practice "
            f"to strengthen conceptual fluency."
        )
        return log_and_format_decision(db, learner_id, target_concept_id, target_concept.name, action, reason, False, {
            "mastery_score": c_mastery,
            "evidence_count": c_state.evidence_count,
        })

    # -------------------------------------------------------------
    # RULE 5 & 6: Challenge vs Advance (Mastery >= 0.85)
    # -------------------------------------------------------------
    # Inspect recent performance metrics
    recent_conf = [a.confidence for a in recent_attempts[:3]]
    avg_conf = sum(recent_conf) / len(recent_conf) if recent_conf else 3.0
    all_recent_correct = all(a.correct for a in recent_attempts[:3]) if recent_attempts else False

    if c_mastery >= MASTERY_PROFICIENCY_THRESHOLD:
        if avg_conf >= 4.0 and all_recent_correct and len(recent_attempts) >= 3:
            action = "Challenge"
            reason = (
                f"Exceptional mastery confirmed on '{target_concept.name}' ({c_mastery*100:.1f}%). "
                f"Learner showed high confidence ({avg_conf:.1f}/5) and 100% accuracy on last 3 attempts. "
                f"Issuing advanced multi-step challenge to stretch cognitive limits."
            )
            return log_and_format_decision(db, learner_id, target_concept_id, target_concept.name, action, reason, False, {
                "mastery_score": c_mastery,
                "confidence_avg": avg_conf,
            })
        else:
            # Advance to next unmastered concept in DAG
            next_concept = find_next_unmastered_concept(db, learner_id, target_concept)
            if next_concept:
                action = "Advance"
                reason = (
                    f"Mastery achieved on '{target_concept.name}' ({c_mastery*100:.1f}% >= 85%). "
                    f"All prerequisites satisfied. Path unlocks progression to '{next_concept.name}'."
                )
                return log_and_format_decision(db, learner_id, next_concept.id, next_concept.name, action, reason, False, {
                    "completed_concept_id": target_concept_id,
                    "completed_concept_name": target_concept.name,
                    "next_concept_id": next_concept.id,
                })
            else:
                action = "Challenge"
                reason = (
                    f"Top of curriculum reached! Mastery on '{target_concept.name}' is {c_mastery*100:.1f}%. "
                    f"All connected DAG concepts complete. Delivering master-level synthesis challenge."
                )
                return log_and_format_decision(db, learner_id, target_concept_id, target_concept.name, action, reason, False, {
                    "mastery_score": c_mastery,
                })

    # Default fallback
    action = "Practice"
    reason = f"Concept '{target_concept.name}' currently at {c_mastery*100:.1f}% mastery. Practice scheduled."
    return log_and_format_decision(db, learner_id, target_concept_id, target_concept.name, action, reason, False, {})


def select_frontier_concept(db: Session, learner_id: str) -> Concept:
    """
    Traverses the concept DAG topologically to identify the best active frontier concept:
    1. First concept in topological order with mastery < 0.85 whose prerequisites are either
       satisfied (>= 0.50) or actively being remediated.
    """
    all_concepts = db.query(Concept).order_by(Concept.level.asc(), Concept.id.asc()).all()
    if not all_concepts:
        raise ValueError("No concepts found in database.")

    # Check for decayed concepts first (spaced review has high pedagogical value)
    for c in all_concepts:
        s = (
            db.query(MasteryState)
            .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == c.id)
            .first()
        )
        if s and s.decay_applied:
            return c

    # Check for incomplete concepts where prereqs are met
    for c in all_concepts:
        s = (
            db.query(MasteryState)
            .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == c.id)
            .first()
        )
        score = s.mastery_score if s else 0.0
        if score < MASTERY_PROFICIENCY_THRESHOLD:
            # Check if all prereqs are >= 0.50
            prereqs_met = True
            for p in c.prerequisites:
                ps = (
                    db.query(MasteryState)
                    .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == p.id)
                    .first()
                )
                if not ps or ps.mastery_score < PREREQUISITE_MASTERY_THRESHOLD:
                    prereqs_met = False
                    break
            if prereqs_met:
                return c

    # If all unlocked are complete or none met, return first concept with lowest score
    lowest_concept = all_concepts[0]
    lowest_score = 2.0
    for c in all_concepts:
        s = (
            db.query(MasteryState)
            .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == c.id)
            .first()
        )
        sc = s.mastery_score if s else 0.0
        if sc < lowest_score:
            lowest_score = sc
            lowest_concept = c

    return lowest_concept


def find_next_unmastered_concept(db: Session, learner_id: str, current_concept: Concept) -> Optional[Concept]:
    """Finds next dependent concept in the DAG that has not reached 0.85 mastery."""
    # Look at dependents of current concept
    for dep in current_concept.dependent_concepts:
        dep_state = (
            db.query(MasteryState)
            .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == dep.id)
            .first()
        )
        dep_score = dep_state.mastery_score if dep_state else 0.0
        if dep_score < MASTERY_PROFICIENCY_THRESHOLD:
            return dep

    # Look globally for next level concept
    candidates = (
        db.query(Concept)
        .filter(Concept.level >= current_concept.level, Concept.id != current_concept.id)
        .order_by(Concept.level.asc())
        .all()
    )
    for cand in candidates:
        s = (
            db.query(MasteryState)
            .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == cand.id)
            .first()
        )
        score = s.mastery_score if s else 0.0
        if score < MASTERY_PROFICIENCY_THRESHOLD:
            return cand

    return None


def log_and_format_decision(
    db: Session,
    learner_id: str,
    concept_id: str,
    concept_name: str,
    action: str,
    reason_text: str,
    was_teacher_override: bool,
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """Logs the decision in ActionLog and returns the standardized response payload."""
    now = get_utc_now()
    action_log = ActionLog(
        learner_id=learner_id,
        concept_id=concept_id,
        action=action,
        reason_text=reason_text,
        timestamp=now,
        was_teacher_override=was_teacher_override,
    )
    db.add(action_log)
    db.commit()

    return {
        "learner_id": learner_id,
        "concept_id": concept_id,
        "concept_name": concept_name,
        "action": action,
        "reason_text": reason_text,
        "timestamp": now,
        "was_teacher_override": was_teacher_override,
        "metrics": metrics,
    }


def record_teacher_override(
    db: Session,
    learner_id: str,
    concept_id: str,
    action: str,
    teacher_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Teacher overrides the engine's next action.
    Stored with was_teacher_override=True, persisting the audit trail while
    redirecting learner's immediate pedagogical pathway.
    """
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise ValueError(f"Concept '{concept_id}' not found.")

    reason = f"[Teacher Override] Educator directly mandated '{action}' for concept '{concept.name}'."
    if teacher_notes:
        reason += f" Educator Note: \"{teacher_notes}\""

    now = get_utc_now()
    action_log = ActionLog(
        learner_id=learner_id,
        concept_id=concept_id,
        action=action,
        reason_text=reason,
        timestamp=now,
        was_teacher_override=True,
        teacher_notes=teacher_notes,
    )
    db.add(action_log)
    db.commit()

    return {
        "learner_id": learner_id,
        "concept_id": concept_id,
        "concept_name": concept.name,
        "action": action,
        "reason_text": reason,
        "timestamp": now,
        "was_teacher_override": True,
        "teacher_notes": teacher_notes,
        "metrics": {"forced_by_educator": True}
    }
