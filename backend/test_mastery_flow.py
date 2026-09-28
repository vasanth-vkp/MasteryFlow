"""
MasteryFlow - Comprehensive Test Suite
======================================
Tests the 5 core scenarios required by YUVA Megathon:
1. Normal correct-streak learner (Advance / Challenge)
2. Prerequisite-weak learner (RemediatePrerequisite barrier)
3. Rapid-guessing learner (Anti-gaming penalty and gain cap)
4. Long-gap learner (Forgetting factor decay and Spaced Review)
5. Teacher override flow (Educator intervention, audit persistence)
"""

import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_utc_now
from app.models import Concept, Learner, Attempt, MasteryState, ActionLog
from app.mastery_engine import (
    calculate_bkt_update,
    record_attempt_and_update_mastery,
    apply_time_decay_if_needed,
    RAPID_GUESS_THRESHOLD_SECONDS,
)
from app.decision_engine import (
    evaluate_next_action,
    record_teacher_override,
    PREREQUISITE_MASTERY_THRESHOLD,
    MASTERY_PROFICIENCY_THRESHOLD,
)

# Use an in-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed minimal concept DAG
    # Arithmetic -> Fractions -> Ratios
    c_arith = Concept(id="c_arithmetic", name="Arithmetic", description="Basic Math", level=1)
    c_frac = Concept(id="c_fractions", name="Fractions", description="Fraction Math", level=2)
    c_ratio = Concept(id="c_ratios", name="Ratios", description="Ratio Math", level=3)

    db.add_all([c_arith, c_frac, c_ratio])
    db.flush()

    c_frac.prerequisites.append(c_arith)
    c_ratio.prerequisites.append(c_frac)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ----------------------------------------------------------------------
# TEST CASE 1: Normal Correct-Streak Learner (Advance / Challenge)
# ----------------------------------------------------------------------
def test_case_1_normal_correct_streak(db_session):
    """
    Learner submits consecutive correct, confident, well-paced responses.
    Verifies mastery monotonically increases past proficiency (85%)
    and triggers 'Challenge' or 'Advance'.
    """
    learner = Learner(id="test_learner_1", name="Streak Student")
    db_session.add(learner)
    
    # Pre-qualify prerequisite
    db_session.add(MasteryState(
        learner_id="test_learner_1",
        concept_id="c_arithmetic",
        mastery_score=0.92,
        raw_mastery_before_decay=0.92,
        evidence_count=5,
        last_updated=get_utc_now(),
    ))
    db_session.commit()

    # Submit 4 strong attempts on c_fractions
    current_time = get_utc_now() - datetime.timedelta(minutes=30)
    for i in range(4):
        attempt_time = current_time + datetime.timedelta(minutes=i * 5)
        attempt, state, breakdown = record_attempt_and_update_mastery(
            db=db_session,
            learner_id="test_learner_1",
            concept_id="c_fractions",
            correct=True,
            confidence=5,
            response_time_ms=18000,
            hint_used=False,
            difficulty="medium",
            custom_timestamp=attempt_time
        )
        assert breakdown["delta"] >= 0, "Mastery must increase on correct attempt"
        assert attempt.is_rapid_guess is False, "Well-paced attempts must not be flagged as gaming"

    final_state = db_session.query(MasteryState).filter(
        MasteryState.learner_id == "test_learner_1",
        MasteryState.concept_id == "c_fractions"
    ).first()

    assert final_state.mastery_score >= MASTERY_PROFICIENCY_THRESHOLD, (
        f"Mastery ({final_state.mastery_score}) should exceed proficiency threshold (0.85)"
    )

    decision = evaluate_next_action(db_session, "test_learner_1", "c_fractions")
    assert decision["action"] in ("Challenge", "Advance"), (
        f"Expected Challenge or Advance, got {decision['action']}"
    )
    assert "Fractions" in decision["reason_text"]
    assert decision["concept_id"] == "c_fractions"
    assert "mastery" in decision["reason_text"].lower()


# ----------------------------------------------------------------------
# TEST CASE 2: Prerequisite-Weak Learner (RemediatePrerequisite barrier)
# ----------------------------------------------------------------------
def test_case_2_prerequisite_weak_learner(db_session):
    """
    Learner attempts target concept 'c_ratios', but prerequisite 'c_fractions'
    is below the 50% threshold.
    Verifies that policy strictly blocks progression and recommends
    'RemediatePrerequisite' with exact numeric justification.
    """
    learner = Learner(id="test_learner_2", name="Gapped Student")
    db_session.add(learner)

    # Prerequisite c_fractions is at 34% (< 50% barrier)
    db_session.add(MasteryState(
        learner_id="test_learner_2",
        concept_id="c_fractions",
        mastery_score=0.34,
        raw_mastery_before_decay=0.34,
        evidence_count=3,
        last_updated=get_utc_now(),
    ))
    db_session.commit()

    decision = evaluate_next_action(db_session, "test_learner_2", "c_ratios")

    assert decision["action"] == "RemediatePrerequisite", (
        f"Expected RemediatePrerequisite, got {decision['action']}"
    )
    assert "Fractions" in decision["reason_text"]
    assert "34.0%" in decision["reason_text"]
    assert decision["metrics"]["blocking_prerequisite_id"] == "c_fractions"


# ----------------------------------------------------------------------
# TEST CASE 3: Rapid-Guessing Learner (Anti-Gaming Detection)
# ----------------------------------------------------------------------
def test_case_3_anti_gaming_rapid_guessing(db_session):
    """
    Learner submits consecutive attempts on the same concept less than 10 seconds apart.
    Verifies:
    1. Flagged as is_rapid_guess = True
    2. Evidence weight penalized to 0.15 (85% reduction)
    3. Mastery delta is tightly capped (<= +0.025)
    """
    learner = Learner(id="test_learner_3", name="Speed Spammer")
    db_session.add(learner)
    db_session.commit()

    base_time = get_utc_now()

    # Attempt 1: Normal attempt
    att1, state1, b1 = record_attempt_and_update_mastery(
        db=db_session,
        learner_id="test_learner_3",
        concept_id="c_arithmetic",
        correct=True,
        confidence=3,
        response_time_ms=12000,
        hint_used=False,
        difficulty="medium",
        custom_timestamp=base_time
    )
    assert att1.is_rapid_guess is False

    # Attempt 2: Submitted only 4 seconds later (Anti-gaming violation!)
    rapid_time = base_time + datetime.timedelta(seconds=4)
    att2, state2, b2 = record_attempt_and_update_mastery(
        db=db_session,
        learner_id="test_learner_3",
        concept_id="c_arithmetic",
        correct=True,
        confidence=3,
        response_time_ms=2500,
        hint_used=False,
        difficulty="medium",
        custom_timestamp=rapid_time
    )

    assert att2.is_rapid_guess is True, "Attempt under 10s must be marked as rapid guess"
    assert att2.evidence_weight <= 0.20, f"Evidence weight should be discounted, got {att2.evidence_weight}"
    assert b2["delta"] <= 0.026, f"Mastery gain should be capped at <= 0.025, got {b2['delta']}"


# ----------------------------------------------------------------------
# TEST CASE 4: Long-Gap Learner (Time-Decay & Spaced Review)
# ----------------------------------------------------------------------
def test_case_4_long_gap_time_decay(db_session):
    """
    Learner attained 86% mastery, but concept was inactive for 20 days.
    Verifies:
    1. Ebbinghaus decay function reduces mastery score.
    2. decay_applied flag becomes True.
    3. Next-Action Engine recommends 'Review' with retention gap explanation.
    """
    learner = Learner(id="test_learner_4", name="Absent Student")
    db_session.add(learner)

    past_date = get_utc_now() - datetime.timedelta(days=20)
    state = MasteryState(
        learner_id="test_learner_4",
        concept_id="c_arithmetic",
        mastery_score=0.86,
        raw_mastery_before_decay=0.86,
        evidence_count=6,
        last_updated=past_date,
        decay_applied=False,
    )
    db_session.add(state)
    db_session.commit()

    # Trigger decay check
    decayed_score, decay_applied = apply_time_decay_if_needed(state)
    assert decay_applied is True, "Decay must apply after 20 days of inactivity (> 7 day threshold)"
    assert decayed_score < 0.86, f"Decayed score ({decayed_score}) should be lower than original (0.86)"

    # Check next action recommendation
    decision = evaluate_next_action(db_session, "test_learner_4", "c_arithmetic")
    assert decision["action"] == "Review", f"Expected Review action, got {decision['action']}"
    assert "decayed" in decision["reason_text"].lower() or "retention" in decision["reason_text"].lower()


# ----------------------------------------------------------------------
# TEST CASE 5: Teacher Override Flow
# ----------------------------------------------------------------------
def test_case_5_teacher_override_flow(db_session):
    """
    Teacher forcefully overrides system recommendation.
    Verifies:
    1. Logged with was_teacher_override = True.
    2. Reason incorporates educator note.
    3. evaluate_next_action returns the overridden directive.
    4. State continues seamlessly.
    """
    learner = Learner(id="test_learner_5", name="Guided Student")
    db_session.add(learner)
    db_session.commit()

    # Educator overrides next action on c_arithmetic to 'Review'
    override_result = record_teacher_override(
        db=db_session,
        learner_id="test_learner_5",
        concept_id="c_arithmetic",
        action="Review",
        teacher_notes="Oral assessment showed minor hesitation on order of operations."
    )

    assert override_result["action"] == "Review"
    assert override_result["was_teacher_override"] is True

    # Check that Next Action Engine honors the override
    next_action = evaluate_next_action(db_session, "test_learner_5", "c_arithmetic")
    assert next_action["was_teacher_override"] is True
    assert next_action["action"] == "Review"
    assert "Oral assessment" in next_action["reason_text"]

    # ActionLog audit trail check
    logged = db_session.query(ActionLog).filter(
        ActionLog.learner_id == "test_learner_5",
        ActionLog.was_teacher_override == True
    ).first()
    assert logged is not None
    assert logged.teacher_notes == "Oral assessment showed minor hesitation on order of operations."
