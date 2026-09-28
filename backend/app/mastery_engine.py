"""
MasteryFlow - Explainable Bayesian Knowledge Tracing & Cognitive Mastery Engine
================================================================================
This module implements an inspectable, deterministic, and explainable update rule
for learner concept mastery.

Mathematical Formulation:
-------------------------
We employ an extended Bayesian Knowledge Tracing (BKT) model augmented with
cognitive evidence weights (Confidence, Response Time, Hint Usage, Difficulty,
Anti-Gaming session caps, and Ebbinghaus-inspired Time Decay).

Standard BKT state update:
  Prior mastery: P(L_t-1)
  
  1. Posterior update based on observation O_t in {0, 1}:
     If Correct (O_t = 1):
       P(L_t | O_t = 1) = [ P(L_t-1) * (1 - P(S)) ] / [ P(L_t-1) * (1 - P(S)) + (1 - P(L_t-1)) * P(G) ]
       
     If Incorrect (O_t = 0):
       P(L_t | O_t = 0) = [ P(L_t-1) * P(S) ] / [ P(L_t-1) * P(S) + (1 - P(L_t-1)) * (1 - P(G)) ]

  2. Contextual Modulations on Guess P(G) and Slip P(S):
     - Hint Used: P(G) jumps to 0.75 (high likelihood user received the answer).
     - Low Confidence (1-2) + Correct: P(G) elevated to 0.60 (lucky guess discount).
     - High Confidence (4-5) + Correct: P(G) lowered to 0.10 (strong authentic signal).
     - High Confidence (5) + Incorrect: P(S) lowered to 0.04 (misconception flag).
     - Response Time (RT):
         If RT < 3.5s and correct: P(G) elevated to 0.70 (rapid guess penalty).
         If RT > 90s: Cognitive struggle detected, transition P(T) discounted.

  3. Learning Transition:
     P(L_t+1) = P(L_t | O_t) + (1 - P(L_t | O_t)) * P(T) * evidence_weight

  4. Anti-Gaming Session Throttling:
     - Rapid-fire attempts (< 10s between same concept attempts) receive an 85% discount
       (evidence_weight = 0.15) and per-attempt positive gain is capped at +0.02.

  5. Time-Decay / Forgetting Factor (Ebbinghaus curve):
     - If delta_days > 7 days since last attempt:
       decay_ratio = exp( - lambda * (delta_days - 7) ), lambda = 0.05
       M_decayed = M_baseline + (M_raw - M_baseline) * decay_ratio
"""

import math
import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from .models import Attempt, MasteryState, Concept
from .database import get_utc_now

# Baseline BKT hyperparameters
BASE_P_T = 0.18   # Base probability of skill transition / learning
BASE_P_G = 0.20   # Base probability of guessing correctly without mastery
BASE_P_S = 0.10   # Base probability of slipping (careless error while knowing concept)
MIN_MASTERY = 0.02
MAX_MASTERY = 0.99
RAPID_GUESS_THRESHOLD_SECONDS = 10.0
MEMORY_DECAY_DAYS_THRESHOLD = 7.0
DECAY_LAMBDA = 0.05
BASELINE_RETENTION = 0.35

DIFFICULTY_TRANSITION_WEIGHTS = {
    "easy": 0.12,
    "medium": 0.18,
    "hard": 0.25,
}

BENCHMARK_RESPONSE_TIMES = {
    "easy": 10000,    # 10s benchmark
    "medium": 25000,  # 25s benchmark
    "hard": 50000,    # 50s benchmark
}


def apply_time_decay_if_needed(
    mastery_state: MasteryState,
    current_time: Optional[datetime.datetime] = None
) -> Tuple[float, bool]:
    """
    Applies Ebbinghaus forgetting decay if a concept hasn't been practiced in > 7 days.
    Returns: (adjusted_mastery_score, decay_applied_flag)
    """
    if current_time is None:
        current_time = get_utc_now()

    delta = current_time - mastery_state.last_updated
    delta_days = delta.total_seconds() / 86400.0

    raw_score = mastery_state.raw_mastery_before_decay or mastery_state.mastery_score

    if delta_days > MEMORY_DECAY_DAYS_THRESHOLD and raw_score > BASELINE_RETENTION:
        decay_period = delta_days - MEMORY_DECAY_DAYS_THRESHOLD
        decay_ratio = math.exp(-DECAY_LAMBDA * decay_period)
        decayed_score = BASELINE_RETENTION + (raw_score - BASELINE_RETENTION) * decay_ratio
        decayed_score = max(MIN_MASTERY, min(decayed_score, raw_score))
        return round(decayed_score, 4), True
    
    return raw_score, False


def detect_anti_gaming(
    db: Session,
    learner_id: str,
    concept_id: str,
    current_timestamp: datetime.datetime
) -> Tuple[bool, float, str]:
    """
    Checks if the user is spamming or gaming attempts:
    1. Rapid-fire submission: attempt on same concept < 10 seconds after previous.
    2. Identical rapid alternation.
    Returns: (is_rapid_guess, evidence_weight, reason_note)
    """
    last_attempt = (
        db.query(Attempt)
        .filter(Attempt.learner_id == learner_id, Attempt.concept_id == concept_id)
        .order_by(Attempt.timestamp.desc())
        .first()
    )

    if not last_attempt:
        return False, 1.0, "Initial evidence"

    delta_seconds = (current_timestamp - last_attempt.timestamp).total_seconds()
    if delta_seconds < RAPID_GUESS_THRESHOLD_SECONDS:
        # Rapid attempt detected: heavily downweight evidence
        evidence_weight = 0.15
        reason = f"Rapid attempt detected ({delta_seconds:.1f}s < 10s threshold). Evidence weight penalized to 15%."
        return True, evidence_weight, reason

    # Check last 3 attempts for uniform guessing pattern
    recent_attempts = (
        db.query(Attempt)
        .filter(Attempt.learner_id == learner_id, Attempt.concept_id == concept_id)
        .order_by(Attempt.timestamp.desc())
        .limit(3)
        .all()
    )
    if len(recent_attempts) >= 3:
        # Check if all had response time < 4 seconds
        all_flash = all(a.response_time_ms < 4000 for a in recent_attempts)
        if all_flash:
            evidence_weight = 0.25
            reason = "Consistent flash-guessing detected (<4s on last 3 attempts). Evidence weight penalized to 25%."
            return True, evidence_weight, reason

    return False, 1.0, "Normal cognitive pacing"


def calculate_bkt_update(
    prior_mastery: float,
    correct: bool,
    confidence: int,
    response_time_ms: int,
    hint_used: bool,
    difficulty: str,
    evidence_weight: float = 1.0,
    is_rapid_guess: bool = False
) -> Dict[str, Any]:
    """
    Executes the Bayesian Knowledge Tracing update with cognitive factor modulations.
    Returns detailed factors breakdown for absolute transparency and explainability.
    """
    # 1. Base parameters
    p_g = BASE_P_G
    p_s = BASE_P_S
    p_t = DIFFICULTY_TRANSITION_WEIGHTS.get(difficulty.lower(), BASE_P_T)

    factors_log = []

    # 2. Adjust Guess Probability P(G) based on Hint & Confidence & Response Time
    if hint_used:
        p_g = 0.75
        factors_log.append("Hint was used (Guess likelihood P(G) boosted to 0.75)")
    else:
        if confidence == 1:
            p_g = 0.55
            factors_log.append("Low confidence (1/5) indicates high guessing likelihood (P(G) = 0.55)")
        elif confidence == 2:
            p_g = 0.35
            factors_log.append("Tentative confidence (2/5) modest guess adjustment (P(G) = 0.35)")
        elif confidence >= 4:
            p_g = 0.10
            factors_log.append("High confidence (4-5/5) lowers guess probability (P(G) = 0.10)")

    # Response Time modulations
    bench_time = BENCHMARK_RESPONSE_TIMES.get(difficulty.lower(), 25000)
    if response_time_ms < 3500 and correct and not hint_used:
        # Impossibly fast correct response -> likely blind guess
        p_g = max(p_g, 0.70)
        factors_log.append(f"Very fast correct response ({response_time_ms/1000:.1f}s) treated as likely guess (P(G)=0.70)")
    elif response_time_ms > (bench_time * 2.5):
        # Hesitation / heavy cognitive friction
        p_t = p_t * 0.70
        factors_log.append(f"Prolonged response time ({response_time_ms/1000:.1f}s) indicates cognitive friction; transition rate reduced")

    # 3. Adjust Slip Probability P(S) based on Misconceptions
    if not correct:
        if confidence >= 4:
            # Overconfident mistake: indicates an ingrained misconception rather than careless slip
            p_s = 0.04
            factors_log.append("High-confidence mistake indicates deep misconception (Slip P(S) lowered to 0.04)")
        elif confidence <= 2:
            p_s = 0.18
            factors_log.append("Low-confidence mistake aligns with uncertainty (P(S) = 0.18)")

    # 4. Bayesian Posterior Update: P(L_t | Observation)
    p_prior = max(MIN_MASTERY, min(prior_mastery, MAX_MASTERY))
    
    if correct:
        # Numerator: P(L) * (1 - S)
        num = p_prior * (1.0 - p_s)
        # Denominator: P(L) * (1 - S) + (1 - P(L)) * G
        den = num + ((1.0 - p_prior) * p_g)
        p_posterior = num / den if den > 0 else p_prior
    else:
        # Numerator: P(L) * S
        num = p_prior * p_s
        # Denominator: P(L) * S + (1 - P(L)) * (1 - G)
        den = num + ((1.0 - p_prior) * (1.0 - p_g))
        p_posterior = num / den if den > 0 else p_prior

    # 5. Learning Transition Update with Evidence Weight:
    effective_p_t = p_t * evidence_weight
    new_mastery = p_posterior + ((1.0 - p_posterior) * effective_p_t)

    # 6. Anti-gaming gain cap
    if is_rapid_guess and correct:
        max_allowed = p_prior + 0.025
        if new_mastery > max_allowed:
            factors_log.append(f"Anti-gaming rule enforced: mastery gain capped at +0.025 (clamped from {new_mastery:.3f} to {max_allowed:.3f})")
            new_mastery = max_allowed

    new_mastery = round(max(MIN_MASTERY, min(new_mastery, MAX_MASTERY)), 4)
    delta = round(new_mastery - prior_mastery, 4)

    return {
        "prior_mastery": round(p_prior, 4),
        "posterior_mastery": new_mastery,
        "delta": delta,
        "p_g_used": round(p_g, 3),
        "p_s_used": round(p_s, 3),
        "effective_p_t": round(effective_p_t, 3),
        "evidence_weight": round(evidence_weight, 2),
        "factors_log": factors_log,
        "explanation": f"BKT update: Prior {p_prior*100:.1f}% -> Posterior {new_mastery*100:.1f}% (Δ: {delta*100:+.1f}%). Factors: {'; '.join(factors_log)}"
    }


def record_attempt_and_update_mastery(
    db: Session,
    learner_id: str,
    concept_id: str,
    correct: bool,
    confidence: int,
    response_time_ms: int,
    hint_used: bool,
    difficulty: str,
    custom_timestamp: Optional[datetime.datetime] = None
) -> Tuple[Attempt, MasteryState, Dict[str, Any]]:
    """
    Core end-to-end atomic service:
    1. Checks anti-gaming constraints.
    2. Retrieves current MasteryState (or initializes with prior).
    3. Runs BKT update.
    4. Persists Attempt and updated MasteryState in SQLite.
    Returns: (attempt_model, mastery_state_model, factor_breakdown)
    """
    now = custom_timestamp or get_utc_now()

    # Step 1: Anti-gaming check
    is_rapid_guess, evidence_weight, gaming_reason = detect_anti_gaming(
        db=db,
        learner_id=learner_id,
        concept_id=concept_id,
        current_timestamp=now
    )

    # Step 2: Record Attempt
    attempt = Attempt(
        learner_id=learner_id,
        concept_id=concept_id,
        correct=correct,
        confidence=confidence,
        response_time_ms=response_time_ms,
        hint_used=hint_used,
        difficulty=difficulty,
        timestamp=now,
        is_rapid_guess=is_rapid_guess,
        evidence_weight=evidence_weight,
    )
    db.add(attempt)
    db.flush()

    # Step 3: Fetch or Create MasteryState
    mastery_state = (
        db.query(MasteryState)
        .filter(MasteryState.learner_id == learner_id, MasteryState.concept_id == concept_id)
        .first()
    )

    if not mastery_state:
        prior_score = 0.15  # Cold prior for brand new unattempted concept
        mastery_state = MasteryState(
            learner_id=learner_id,
            concept_id=concept_id,
            mastery_score=prior_score,
            raw_mastery_before_decay=prior_score,
            evidence_count=0,
            last_updated=now,
            decay_applied=False,
        )
        db.add(mastery_state)
        db.flush()
    else:
        # Check if decay was present
        prior_score = mastery_state.mastery_score

    # Step 4: Calculate BKT update
    breakdown = calculate_bkt_update(
        prior_mastery=prior_score,
        correct=correct,
        confidence=confidence,
        response_time_ms=response_time_ms,
        hint_used=hint_used,
        difficulty=difficulty,
        evidence_weight=evidence_weight,
        is_rapid_guess=is_rapid_guess,
    )

    # Step 5: Update state
    mastery_state.mastery_score = breakdown["posterior_mastery"]
    mastery_state.raw_mastery_before_decay = breakdown["posterior_mastery"]
    mastery_state.evidence_count += 1
    mastery_state.last_updated = now
    mastery_state.decay_applied = False  # Fresh attempt clears active decay

    db.commit()
    db.refresh(attempt)
    db.refresh(mastery_state)

    return attempt, mastery_state, breakdown
