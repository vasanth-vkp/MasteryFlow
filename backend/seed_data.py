"""
MasteryFlow - Seed Data Script
==============================
Initializes:
1. Complete 10-concept Algebra DAG with multi-level prerequisite chains.
2. Question bank with real math prompts, options, hints, and explanations.
3. Pre-loaded demo learner profiles:
   - Learner A (Aria Chen): High performer (fast, confident, correct, strong prereqs)
   - Learner B (Bilal Tariq): Struggling learner (low confidence, hints, weak prereqs)
   - Learner C (Chloe Dupont): Stuck learner requiring TeacherIntervention
   - Learner D (Devon Miller): Inactive learner triggering Time-Decay Review
"""

import os
import json
import datetime
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base, get_utc_now
from app.models import Concept, Learner, Attempt, MasteryState, ActionLog, DiagnosticQuestion
from app.mastery_engine import record_attempt_and_update_mastery
from app.decision_engine import evaluate_next_action, record_teacher_override

def seed_database():
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        print("Seeding concept DAG...")
        # 1. Create Concepts
        c_arithmetic = Concept(
            id="c_arithmetic",
            name="Arithmetic & Operations",
            description="Foundational arithmetic operations: addition, subtraction, multiplication, division, and order of operations.",
            subject="Basic Algebra",
            level=1,
        )
        c_integers = Concept(
            id="c_integers",
            name="Integers & Signed Numbers",
            description="Positive and negative numbers, number line operations, and absolute values.",
            subject="Basic Algebra",
            level=1,
        )
        c_fractions = Concept(
            id="c_fractions",
            name="Fractions & Decimals",
            description="Fractional arithmetic, common denominators, decimal conversions, and proportions.",
            subject="Basic Algebra",
            level=2,
        )
        c_variables = Concept(
            id="c_variables",
            name="Variables & Expressions",
            description="Algebraic variables, simplifying expressions, combining like terms, and evaluation.",
            subject="Basic Algebra",
            level=2,
        )
        c_ratios = Concept(
            id="c_ratios",
            name="Ratios & Proportions",
            description="Unit rates, proportional relationships, scale factors, and cross-multiplication.",
            subject="Basic Algebra",
            level=3,
        )
        c_percentages = Concept(
            id="c_percentages",
            name="Percentages & Rates",
            description="Percent calculations, interest rates, percentage change, and financial applications.",
            subject="Basic Algebra",
            level=4,
        )
        c_one_step_eq = Concept(
            id="c_one_step_eq",
            name="One-Step Linear Equations",
            description="Solving single-variable linear equations using single inverse operations.",
            subject="Basic Algebra",
            level=3,
        )
        c_two_step_eq = Concept(
            id="c_two_step_eq",
            name="Two-Step Equations",
            description="Equations requiring isolation through multiple inverse operations (addition/subtraction then multiplication/division).",
            subject="Basic Algebra",
            level=4,
        )
        c_multi_step_eq = Concept(
            id="c_multi_step_eq",
            name="Multi-Step & Fractional Equations",
            description="Equations with distributive property, clearing fractions, and variables on both sides.",
            subject="Basic Algebra",
            level=5,
        )
        c_inequalities = Concept(
            id="c_inequalities",
            name="Linear Inequalities",
            description="Solving and graphing single and multi-step inequalities, sign reversal rules on division by negatives.",
            subject="Basic Algebra",
            level=5,
        )

        db.add_all([
            c_arithmetic, c_integers, c_fractions, c_variables,
            c_ratios, c_percentages, c_one_step_eq, c_two_step_eq,
            c_multi_step_eq, c_inequalities
        ])
        db.flush()

        # Connect Prerequisite DAG Edges
        # Fractions requires Arithmetic
        c_fractions.prerequisites.append(c_arithmetic)
        # Variables requires Arithmetic and Integers
        c_variables.prerequisites.append(c_arithmetic)
        c_variables.prerequisites.append(c_integers)
        # Ratios requires Fractions
        c_ratios.prerequisites.append(c_fractions)
        # Percentages requires Ratios
        c_percentages.prerequisites.append(c_ratios)
        # One-Step Equations requires Variables and Arithmetic
        c_one_step_eq.prerequisites.append(c_variables)
        c_one_step_eq.prerequisites.append(c_arithmetic)
        # Two-Step Equations requires One-Step Equations and Integers
        c_two_step_eq.prerequisites.append(c_one_step_eq)
        c_two_step_eq.prerequisites.append(c_integers)
        # Multi-Step Equations requires Two-Step Equations and Fractions
        c_multi_step_eq.prerequisites.append(c_two_step_eq)
        c_multi_step_eq.prerequisites.append(c_fractions)
        # Inequalities requires Two-Step Equations and Integers
        c_inequalities.prerequisites.append(c_two_step_eq)
        c_inequalities.prerequisites.append(c_integers)

        db.commit()
        print("Concept DAG seeded successfully with 10 concepts and multi-level prerequisites.")

        # 2. Seed Question Bank for Practice Simulator & Diagnostic
        print("Seeding questions bank...")
        question_bank = [
            # Arithmetic
            {
                "id": "q_arith_1",
                "concept_id": "c_arithmetic",
                "prompt": "Evaluate the expression: 48 ÷ (6 + 2) × 3",
                "options": ["18", "2", "8", "24"],
                "correct_answer": "18",
                "explanation": "Parentheses first: (6 + 2) = 8. Then left-to-right: 48 ÷ 8 = 6, and 6 × 3 = 18.",
                "difficulty": "easy",
                "hint_text": "Remember PEMDAS / BODMAS: perform parentheses first, then division and multiplication left to right."
            },
            {
                "id": "q_arith_2",
                "concept_id": "c_arithmetic",
                "prompt": "Compute: 15 × 4 - 36 ÷ 3 + 7",
                "options": ["55", "52", "61", "48"],
                "correct_answer": "55",
                "explanation": "Multiplication & division: 15 × 4 = 60, 36 ÷ 3 = 12. Then 60 - 12 + 7 = 55.",
                "difficulty": "medium",
                "hint_text": "Calculate multiplication (15 × 4) and division (36 ÷ 3) before adding and subtracting."
            },
            # Integers
            {
                "id": "q_int_1",
                "concept_id": "c_integers",
                "prompt": "Calculate: -14 - (-8) + (-6)",
                "options": ["-12", "-28", "0", "-4"],
                "correct_answer": "-12",
                "explanation": "-14 - (-8) becomes -14 + 8 = -6. Then -6 + (-6) = -12.",
                "difficulty": "easy",
                "hint_text": "Subtracting a negative is the same as adding a positive: -(-8) = +8."
            },
            {
                "id": "q_int_2",
                "concept_id": "c_integers",
                "prompt": "Evaluate: (-3) × (-4) × (-2)",
                "options": ["-24", "24", "-12", "18"],
                "correct_answer": "-24",
                "explanation": "(-3) × (-4) = +12. Then 12 × (-2) = -24.",
                "difficulty": "medium",
                "hint_text": "Negative times negative is positive, then positive times negative is negative."
            },
            # Fractions
            {
                "id": "q_frac_1",
                "concept_id": "c_fractions",
                "prompt": "Add and simplify to lowest terms: 3/4 + 2/5",
                "options": ["23/20", "5/9", "1 1/4", "15/8"],
                "correct_answer": "23/20",
                "explanation": "Common denominator is 20: 15/20 + 8/20 = 23/20.",
                "difficulty": "medium",
                "hint_text": "Find a common denominator for 4 and 5 (which is 20) before adding the numerators."
            },
            {
                "id": "q_frac_2",
                "concept_id": "c_fractions",
                "prompt": "Multiply and simplify: 5/6 × 9/10",
                "options": ["3/4", "45/60", "1/2", "7/12"],
                "correct_answer": "3/4",
                "explanation": "Multiply numerators and denominators: (5 × 9) / (6 × 10) = 45/60 = 3/4.",
                "difficulty": "medium",
                "hint_text": "Multiply numerators together and denominators together, or cross-cancel 5/10 and 9/6 first."
            },
            # Variables
            {
                "id": "q_var_1",
                "concept_id": "c_variables",
                "prompt": "If a = 3 and b = -2, evaluate the algebraic expression: 2a² - 4b",
                "options": ["26", "10", "22", "-10"],
                "correct_answer": "26",
                "explanation": "a² = 3² = 9. 2(9) = 18. -4b = -4(-2) = +8. 18 + 8 = 26.",
                "difficulty": "medium",
                "hint_text": "Square 3 first to get 9, then multiply by 2. Watch the negative signs when multiplying -4 by -2."
            },
            # Ratios
            {
                "id": "q_ratio_1",
                "concept_id": "c_ratios",
                "prompt": "A paint mix requires 3 parts blue to 5 parts yellow. To mix 40 liters total, how many liters of blue paint are needed?",
                "options": ["15 liters", "24 liters", "12 liters", "20 liters"],
                "correct_answer": "15 liters",
                "explanation": "Total parts = 3 + 5 = 8 parts. Each part = 40 ÷ 8 = 5 liters. Blue = 3 parts × 5 = 15 liters.",
                "difficulty": "medium",
                "hint_text": "Find the total number of parts in the ratio first, then determine the value of one part."
            },
            {
                "id": "q_ratio_2",
                "concept_id": "c_ratios",
                "prompt": "If 4 pencils cost $2.80, what is the cost of 7 pencils at the same unit rate?",
                "options": ["$4.90", "$4.20", "$5.60", "$3.50"],
                "correct_answer": "$4.90",
                "explanation": "Unit rate = $2.80 / 4 = $0.70 per pencil. 7 × $0.70 = $4.90.",
                "difficulty": "easy",
                "hint_text": "Calculate the price of a single pencil first, then multiply by 7."
            },
            # Percentages
            {
                "id": "q_pct_1",
                "concept_id": "c_percentages",
                "prompt": "A jacket originally priced at $80 is on sale for 25% off. What is the sale price?",
                "options": ["$60", "$65", "$55", "$70"],
                "correct_answer": "$60",
                "explanation": "Discount = 25% of $80 = $20. Sale price = $80 - $20 = $60.",
                "difficulty": "medium",
                "hint_text": "Find 25% of 80 (which is 1/4 of 80), then subtract that discount from 80."
            },
            # One-Step
            {
                "id": "q_one_1",
                "concept_id": "c_one_step_eq",
                "prompt": "Solve for x: -7x = 63",
                "options": ["x = -9", "x = 9", "x = -70", "x = 56"],
                "correct_answer": "x = -9",
                "explanation": "Divide both sides by -7: x = 63 / -7 = -9.",
                "difficulty": "medium",
                "hint_text": "Isolate x by dividing both sides of the equation by the coefficient -7."
            },
            # Two-Step
            {
                "id": "q_two_1",
                "concept_id": "c_two_step_eq",
                "prompt": "Solve for y: 3y - 7 = 14",
                "options": ["y = 7", "y = 21/3", "y = 9", "y = 5"],
                "correct_answer": "y = 7",
                "explanation": "Add 7 to both sides: 3y = 21. Divide by 3: y = 7.",
                "difficulty": "medium",
                "hint_text": "First add 7 to both sides of the equation, then divide both sides by 3."
            },
            # Multi-Step
            {
                "id": "q_multi_1",
                "concept_id": "c_multi_step_eq",
                "prompt": "Solve for w: 2(w - 4) + 3w = 22",
                "options": ["w = 6", "w = 5", "w = 7", "w = 4"],
                "correct_answer": "w = 6",
                "explanation": "Expand: 2w - 8 + 3w = 22 -> 5w - 8 = 22 -> 5w = 30 -> w = 6.",
                "difficulty": "hard",
                "hint_text": "Distribute the 2 through (w - 4), combine like terms (2w + 3w), then isolate w."
            },
            # Inequalities
            {
                "id": "q_ineq_1",
                "concept_id": "c_inequalities",
                "prompt": "Solve: -4z + 5 < 21",
                "options": ["z > -4", "z < -4", "z > 4", "z < 4"],
                "correct_answer": "z > -4",
                "explanation": "Subtract 5: -4z < 16. Divide by -4 (flip inequality sign!): z > -4.",
                "difficulty": "hard",
                "hint_text": "Remember that dividing or multiplying both sides by a negative number flips the inequality symbol!"
            }
        ]

        for q in question_bank:
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
        print(f"Seeded {len(question_bank)} questions.")

        # 3. Seed Demo Learner Profiles
        now = get_utc_now()

        # ------------------------------------------------------------------
        # Learner A: Aria Chen
        # Profile: Fast, confident, authentic mastery, solid prerequisite foundation.
        # Target concept: c_ratios -> receives "Advance" or "Challenge"
        # ------------------------------------------------------------------
        print("Seeding Learner A (Aria Chen)...")
        learner_a = Learner(id="learner_a", name="Aria Chen", created_at=now - datetime.timedelta(days=10))
        db.add(learner_a)
        db.flush()

        # Seed solid prerequisites for Learner A
        # Arithmetic: 0.94
        db.add(MasteryState(
            learner_id="learner_a",
            concept_id="c_arithmetic",
            mastery_score=0.94,
            raw_mastery_before_decay=0.94,
            evidence_count=6,
            last_updated=now - datetime.timedelta(days=2),
            decay_applied=False
        ))
        # Integers: 0.91
        db.add(MasteryState(
            learner_id="learner_a",
            concept_id="c_integers",
            mastery_score=0.91,
            raw_mastery_before_decay=0.91,
            evidence_count=5,
            last_updated=now - datetime.timedelta(days=2),
            decay_applied=False
        ))
        # Fractions (prerequisite of ratios): 0.89 (solid!)
        db.add(MasteryState(
            learner_id="learner_a",
            concept_id="c_fractions",
            mastery_score=0.89,
            raw_mastery_before_decay=0.89,
            evidence_count=5,
            last_updated=now - datetime.timedelta(days=1),
            decay_applied=False
        ))
        # Attempt history on c_ratios for Learner A: 4 confident, correct, fast responses
        db.commit()

        for i, (rt, conf) in enumerate([(14000, 4), (11000, 5), (13000, 5), (12000, 5)]):
            record_attempt_and_update_mastery(
                db=db,
                learner_id="learner_a",
                concept_id="c_ratios",
                correct=True,
                confidence=conf,
                response_time_ms=rt,
                hint_used=False,
                difficulty="medium",
                custom_timestamp=now - datetime.timedelta(minutes=40 - (i * 8))
            )

        # Evaluate decision for Learner A
        evaluate_next_action(db, "learner_a", "c_ratios")

        # ------------------------------------------------------------------
        # Learner B: Bilal Tariq
        # Profile: Struggling, rapid guesses, heavy hint reliance, weak prerequisite!
        # Target concept: c_ratios -> receives "RemediatePrerequisite" (c_fractions is 38%)
        # ------------------------------------------------------------------
        print("Seeding Learner B (Bilal Tariq)...")
        learner_b = Learner(id="learner_b", name="Bilal Tariq", created_at=now - datetime.timedelta(days=5))
        db.add(learner_b)
        db.flush()

        # Weak prerequisite fractions for Bilal: 0.38 (< 50% barrier!)
        db.add(MasteryState(
            learner_id="learner_b",
            concept_id="c_fractions",
            mastery_score=0.38,
            raw_mastery_before_decay=0.38,
            evidence_count=4,
            last_updated=now - datetime.timedelta(days=1),
            decay_applied=False
        ))
        # Seed attempt on c_fractions showing struggle
        db.add(Attempt(
            learner_id="learner_b",
            concept_id="c_fractions",
            correct=False,
            confidence=2,
            response_time_ms=32000,
            hint_used=True,
            difficulty="medium",
            timestamp=now - datetime.timedelta(days=1),
            is_rapid_guess=False,
            evidence_weight=1.0,
        ))
        db.commit()

        # Attempts on c_ratios for Learner B: low confidence, hints used, 1 rapid guess
        # Attempt 1: hint used, slow
        record_attempt_and_update_mastery(
            db=db,
            learner_id="learner_b",
            concept_id="c_ratios",
            correct=True,
            confidence=1,
            response_time_ms=28000,
            hint_used=True,
            difficulty="medium",
            custom_timestamp=now - datetime.timedelta(minutes=30)
        )
        # Attempt 2: incorrect, low confidence
        record_attempt_and_update_mastery(
            db=db,
            learner_id="learner_b",
            concept_id="c_ratios",
            correct=False,
            confidence=2,
            response_time_ms=19000,
            hint_used=True,
            difficulty="medium",
            custom_timestamp=now - datetime.timedelta(minutes=15)
        )
        # Attempt 3: rapid guess (5s later)
        record_attempt_and_update_mastery(
            db=db,
            learner_id="learner_b",
            concept_id="c_ratios",
            correct=False,
            confidence=1,
            response_time_ms=2500,
            hint_used=False,
            difficulty="medium",
            custom_timestamp=now - datetime.timedelta(minutes=14, seconds=55)
        )

        # Evaluate decision for Learner B -> will trigger RemediatePrerequisite for c_fractions!
        evaluate_next_action(db, "learner_b", "c_ratios")

        # ------------------------------------------------------------------
        # Learner C: Chloe Dupont
        # Profile: Persistent failure / stuck learner -> triggers TeacherIntervention
        # ------------------------------------------------------------------
        print("Seeding Learner C (Chloe Dupont)...")
        learner_c = Learner(id="learner_c", name="Chloe Dupont", created_at=now - datetime.timedelta(days=3))
        db.add(learner_c)
        db.flush()

        # 3 consecutive failed attempts on c_two_step_eq with hints
        for i in range(3):
            record_attempt_and_update_mastery(
                db=db,
                learner_id="learner_c",
                concept_id="c_two_step_eq",
                correct=False,
                confidence=2,
                response_time_ms=35000 + (i * 4000),
                hint_used=True,
                difficulty="medium",
                custom_timestamp=now - datetime.timedelta(minutes=25 - (i * 5))
            )

        evaluate_next_action(db, "learner_c", "c_two_step_eq")

        # ------------------------------------------------------------------
        # Learner D: Devon Miller
        # Profile: Inactive learner with Time Decay -> triggers Review (Spaced Repetition)
        # ------------------------------------------------------------------
        print("Seeding Learner D (Devon Miller)...")
        learner_d = Learner(id="learner_d", name="Devon Miller", created_at=now - datetime.timedelta(days=25))
        db.add(learner_d)
        db.flush()

        # Inactive for 18 days on c_integers: was 0.88, now decayed
        decayed_state = MasteryState(
            learner_id="learner_d",
            concept_id="c_integers",
            mastery_score=0.48,
            raw_mastery_before_decay=0.88,
            evidence_count=6,
            last_updated=now - datetime.timedelta(days=18),
            decay_applied=True,
        )
        db.add(decayed_state)
        db.commit()

        evaluate_next_action(db, "learner_d", "c_integers")

        print("\nAll seed data generated successfully!")
        print("Summary of profiles ready for live demo:")
        print("  - Learner A (Aria Chen): High performer -> Action: Challenge / Advance")
        print("  - Learner B (Bilal Tariq): Prerequisite gap -> Action: RemediatePrerequisite (c_fractions)")
        print("  - Learner C (Chloe Dupont): Stuck learner -> Action: TeacherIntervention")
        print("  - Learner D (Devon Miller): 18 days inactive -> Action: Review (Spaced Repetition)")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
