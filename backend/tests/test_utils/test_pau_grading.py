"""
Tests for PAU Grading System utilities
backend/app/utils/pau_grading.py

This is the CORE value proposition of Shadow - PAU-specific grading.
Every grade boundary, classification threshold, and calculation must be verified.
"""
import pytest
from app.utils.pau_grading import (
    convert_score_to_grade,
    get_letter_grade,
    get_grade_point,
    calculate_cgpa,
    get_classification,
    predict_exam_score,
    estimate_participation,
    calculate_course_grade,
    validate_ca_allocation,
    PAUGradingSystem,
    PAU_GRADE_SCALE,
    FIRST_CLASS,
    SECOND_CLASS_UPPER,
    SECOND_CLASS_LOWER,
    THIRD_CLASS,
    CONTINUOUS_ASSESSMENT,
    FINAL_EXAM,
    CA_ASSESSMENTS,
    CA_PARTICIPATION,
)


# ===================================================================
# Constants verification
# ===================================================================

class TestConstants:
    """Verify PAU grading constants are correct"""

    def test_grade_scale_boundaries(self):
        assert FIRST_CLASS == 4.50
        assert SECOND_CLASS_UPPER == 3.50
        assert SECOND_CLASS_LOWER == 2.40
        assert THIRD_CLASS == 1.50

    def test_assessment_structure(self):
        assert CONTINUOUS_ASSESSMENT == 35
        assert FINAL_EXAM == 65
        assert CA_ASSESSMENTS == 30
        assert CA_PARTICIPATION == 5
        assert CA_ASSESSMENTS + CA_PARTICIPATION == CONTINUOUS_ASSESSMENT

    def test_total_assessment_is_100(self):
        assert CONTINUOUS_ASSESSMENT + FINAL_EXAM == 100


# ===================================================================
# convert_score_to_grade
# ===================================================================

class TestConvertScoreToGrade:
    """Test numerical score to PAU grade conversion"""

    # --- Exact boundary tests ---

    def test_score_100_is_A(self):
        result = convert_score_to_grade(100)
        assert result["grade"] == "A"
        assert result["points"] == 5.0

    def test_score_70_is_A(self):
        result = convert_score_to_grade(70)
        assert result["grade"] == "A"
        assert result["points"] == 5.0

    def test_score_69_is_B(self):
        result = convert_score_to_grade(69)
        assert result["grade"] == "B"
        assert result["points"] == 4.0

    def test_score_60_is_B(self):
        result = convert_score_to_grade(60)
        assert result["grade"] == "B"
        assert result["points"] == 4.0

    def test_score_59_is_C(self):
        result = convert_score_to_grade(59)
        assert result["grade"] == "C"
        assert result["points"] == 3.0

    def test_score_50_is_C(self):
        result = convert_score_to_grade(50)
        assert result["grade"] == "C"
        assert result["points"] == 3.0

    def test_score_49_is_D(self):
        result = convert_score_to_grade(49)
        assert result["grade"] == "D"
        assert result["points"] == 2.0

    def test_score_45_is_D(self):
        result = convert_score_to_grade(45)
        assert result["grade"] == "D"
        assert result["points"] == 2.0

    def test_score_44_is_E(self):
        result = convert_score_to_grade(44)
        assert result["grade"] == "E"
        assert result["points"] == 1.0

    def test_score_40_is_E(self):
        result = convert_score_to_grade(40)
        assert result["grade"] == "E"
        assert result["points"] == 1.0

    def test_score_39_is_F(self):
        result = convert_score_to_grade(39)
        assert result["grade"] == "F"
        assert result["points"] == 0.0

    def test_score_0_is_F(self):
        result = convert_score_to_grade(0)
        assert result["grade"] == "F"
        assert result["points"] == 0.0

    # --- Description checks ---

    def test_A_description_is_excellent(self):
        assert convert_score_to_grade(85)["description"] == "Excellent"

    def test_B_description_is_good(self):
        assert convert_score_to_grade(65)["description"] == "Good"

    def test_C_description_is_fair(self):
        assert convert_score_to_grade(55)["description"] == "Fair"

    def test_D_description_is_pass(self):
        assert convert_score_to_grade(47)["description"] == "Pass"

    def test_E_description_is_conditional(self):
        assert convert_score_to_grade(42)["description"] == "Conditional Pass"

    def test_F_description_is_fail(self):
        assert convert_score_to_grade(20)["description"] == "Fail"

    # --- Edge cases ---

    def test_negative_score_raises_error(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            convert_score_to_grade(-5)

    def test_score_above_100_raises_error(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            convert_score_to_grade(105)

    def test_nan_score_raises_error(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            convert_score_to_grade(float('nan'))

    def test_inf_score_raises_error(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            convert_score_to_grade(float('inf'))

    def test_negative_inf_score_raises_error(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            convert_score_to_grade(float('-inf'))

    def test_none_score_raises_error(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            convert_score_to_grade(None)

    # --- Mid-range verification ---

    def test_score_75_is_A(self):
        assert convert_score_to_grade(75)["grade"] == "A"

    def test_score_55_is_C(self):
        assert convert_score_to_grade(55)["grade"] == "C"


# ===================================================================
# get_letter_grade / get_grade_point convenience functions
# ===================================================================

class TestLetterGradeAndGradePoint:

    def test_get_letter_grade_A(self):
        assert get_letter_grade(85) == "A"

    def test_get_letter_grade_B(self):
        assert get_letter_grade(65) == "B"

    def test_get_letter_grade_F(self):
        assert get_letter_grade(10) == "F"

    def test_get_grade_point_A(self):
        assert get_grade_point(70) == 5.0

    def test_get_grade_point_B(self):
        assert get_grade_point(60) == 4.0

    def test_get_grade_point_F(self):
        assert get_grade_point(0) == 0.0


# ===================================================================
# calculate_cgpa
# ===================================================================

class TestCalculateCGPA:

    def test_single_course_A(self):
        courses = [{"grade_point": 5.0, "credits": 3}]
        assert calculate_cgpa(courses) == 5.0

    def test_single_course_F(self):
        courses = [{"grade_point": 0.0, "credits": 3}]
        assert calculate_cgpa(courses) == 0.0

    def test_two_courses_equal_credits(self):
        courses = [
            {"grade_point": 5.0, "credits": 3},
            {"grade_point": 3.0, "credits": 3},
        ]
        # (5*3 + 3*3) / (3+3) = 24/6 = 4.0
        assert calculate_cgpa(courses) == 4.0

    def test_courses_unequal_credits(self):
        courses = [
            {"grade_point": 5.0, "credits": 4},  # 20
            {"grade_point": 3.0, "credits": 2},  # 6
        ]
        # (20 + 6) / (4+2) = 26/6 = 4.33
        assert calculate_cgpa(courses) == 4.33

    def test_empty_courses_returns_zero(self):
        assert calculate_cgpa([]) == 0.0

    def test_zero_credits_returns_zero(self):
        courses = [{"grade_point": 5.0, "credits": 0}]
        assert calculate_cgpa(courses) == 0.0

    def test_realistic_semester(self):
        """Realistic PAU semester: 6 courses, 18 credits"""
        courses = [
            {"grade_point": 5.0, "credits": 3},   # A in CSC401
            {"grade_point": 4.0, "credits": 3},   # B in CSC403
            {"grade_point": 5.0, "credits": 3},   # A in CSC405
            {"grade_point": 3.0, "credits": 3},   # C in MTH401
            {"grade_point": 4.0, "credits": 3},   # B in CSC407
            {"grade_point": 5.0, "credits": 3},   # A in CSC409
        ]
        # (15+12+15+9+12+15) / 18 = 78/18 = 4.33
        assert calculate_cgpa(courses) == 4.33

    def test_missing_keys_handled(self):
        """Courses with missing keys should use 0 defaults"""
        courses = [{"grade_point": 5.0}, {"credits": 3}]
        # First course: 5.0 * 0 = 0, Second: 0 * 3 = 0 → 0/3 = 0.0
        assert calculate_cgpa(courses) == 0.0


# ===================================================================
# get_classification
# ===================================================================

class TestGetClassification:

    def test_first_class_at_boundary(self):
        assert get_classification(4.50) == "First Class"

    def test_first_class_above(self):
        assert get_classification(5.0) == "First Class"

    def test_second_upper_at_boundary(self):
        assert get_classification(3.50) == "Second Class Upper"

    def test_second_upper_below_first(self):
        assert get_classification(4.49) == "Second Class Upper"

    def test_second_lower_at_boundary(self):
        assert get_classification(2.40) == "Second Class Lower"

    def test_second_lower_mid(self):
        assert get_classification(3.0) == "Second Class Lower"

    def test_third_class_at_boundary(self):
        assert get_classification(1.50) == "Third Class"

    def test_third_class_mid(self):
        assert get_classification(2.0) == "Third Class"

    def test_pass_at_boundary(self):
        assert get_classification(1.0) == "Pass"

    def test_fail_below_one(self):
        assert get_classification(0.5) == "Fail"

    def test_fail_at_zero(self):
        assert get_classification(0.0) == "Fail"


# ===================================================================
# predict_exam_score
# ===================================================================

class TestPredictExamScore:

    def test_full_ca_default_difficulty(self):
        # CA=35 → percentage=1.0 → exam_pct=0.85 → exam=0.85*65=55.25
        result = predict_exam_score(35)
        assert result == 55.25

    def test_zero_ca(self):
        assert predict_exam_score(0) == 0.0

    def test_half_ca(self):
        # 17.5/35 = 0.5 → 0.5*0.85 = 0.425 → 0.425*65 = 27.625 → 27.62
        result = predict_exam_score(17.5)
        assert result == 27.62

    def test_high_difficulty(self):
        # CA=35 → pct=1.0 → exam_pct=0.85*1.2=1.02 → 1.02*65=66.3
        result = predict_exam_score(35, course_difficulty=1.2)
        assert result == 66.3

    def test_low_difficulty(self):
        # CA=35 → pct=1.0 → exam_pct=0.85*0.8=0.68 → 0.68*65=44.2
        result = predict_exam_score(35, course_difficulty=0.8)
        assert result == 44.2


# ===================================================================
# estimate_participation
# ===================================================================

class TestEstimateParticipation:

    def test_high_completion_full_marks(self):
        assert estimate_participation(0.85) == 5.0
        assert estimate_participation(0.95) == 5.0
        assert estimate_participation(1.0) == 5.0

    def test_good_completion(self):
        assert estimate_participation(0.70) == 4.0
        assert estimate_participation(0.80) == 4.0

    def test_average_completion(self):
        assert estimate_participation(0.60) == 3.0
        assert estimate_participation(0.65) == 3.0

    def test_below_average(self):
        assert estimate_participation(0.50) == 2.5
        assert estimate_participation(0.0) == 2.5


# ===================================================================
# calculate_course_grade
# ===================================================================

class TestCalculateCourseGrade:

    def test_with_all_scores_provided(self):
        result = calculate_course_grade(
            ca_tasks_score=25,
            participation_score=4,
            exam_score=50,
        )
        # CA = 25 + 4 = 29, Final = 29 + 50 = 79 → A (5.0)
        assert result["ca_score"] == 29
        assert result["exam_score"] == 50
        assert result["final_score"] == 79
        assert result["letter_grade"] == "A"
        assert result["grade_point"] == 5.0

    def test_with_predicted_exam(self):
        result = calculate_course_grade(
            ca_tasks_score=20,
            participation_score=4,
        )
        # CA = 20 + 4 = 24
        # Predicted exam = predict_exam_score(24) → 24/35 * 0.85 * 65
        assert result["ca_score"] == 24
        assert result["exam_score"] > 0  # Should be predicted
        assert "letter_grade" in result

    def test_with_estimated_participation(self):
        result = calculate_course_grade(
            ca_tasks_score=20,
            completion_rate=0.90,
        )
        # Participation = 5.0 (90% completion → ≥85%)
        # CA = 20 + 5 = 25
        assert result["ca_score"] == 25

    def test_ca_capped_at_35(self):
        result = calculate_course_grade(
            ca_tasks_score=32,
            participation_score=5,
            exam_score=60,
        )
        # CA = 32 + 5 = 37 → capped at 35
        assert result["ca_score"] == 35

    def test_final_score_capped_at_100(self):
        result = calculate_course_grade(
            ca_tasks_score=30,
            participation_score=5,
            exam_score=65,
        )
        # 35 + 65 = 100 → cap at 100
        assert result["final_score"] == 100

    def test_zero_ca_zero_exam(self):
        result = calculate_course_grade(
            ca_tasks_score=0,
            participation_score=0,
            exam_score=0,
        )
        assert result["final_score"] == 0
        assert result["letter_grade"] == "F"
        assert result["grade_point"] == 0.0

    def test_borderline_pass_score(self):
        """Score of exactly 40 should give E (Conditional Pass)"""
        result = calculate_course_grade(
            ca_tasks_score=15,
            participation_score=3,
            exam_score=22,
        )
        # 15 + 3 = 18, 18 + 22 = 40 → E (1.0)
        assert result["final_score"] == 40
        assert result["letter_grade"] == "E"
        assert result["grade_point"] == 1.0


# ===================================================================
# validate_ca_allocation
# ===================================================================

class TestValidateCAAllocation:

    def test_valid_allocation(self):
        tasks = [
            {"weight": 15, "category": "CA"},
            {"weight": 10, "category": "CA"},
        ]
        result = validate_ca_allocation(tasks)
        assert result["is_valid"] is True
        assert result["total_allocated"] == 25
        assert result["remaining"] == 5
        assert result["max_ca"] == 30

    def test_exact_allocation(self):
        tasks = [
            {"weight": 15, "category": "CA"},
            {"weight": 15, "category": "CA"},
        ]
        result = validate_ca_allocation(tasks)
        assert result["is_valid"] is True
        assert result["total_allocated"] == 30
        assert result["remaining"] == 0

    def test_over_allocation(self):
        tasks = [
            {"weight": 20, "category": "CA"},
            {"weight": 15, "category": "CA"},
        ]
        result = validate_ca_allocation(tasks)
        assert result["is_valid"] is False
        assert result["total_allocated"] == 35
        assert result["remaining"] == -5

    def test_ignores_exam_tasks(self):
        tasks = [
            {"weight": 15, "category": "CA"},
            {"weight": 65, "category": "EXAM"},
        ]
        result = validate_ca_allocation(tasks)
        assert result["is_valid"] is True
        assert result["total_allocated"] == 15

    def test_empty_tasks(self):
        result = validate_ca_allocation([])
        assert result["is_valid"] is True
        assert result["total_allocated"] == 0
        assert result["remaining"] == 30

    def test_participation_included_in_response(self):
        result = validate_ca_allocation([])
        assert result["participation"] == 5


# ===================================================================
# PAUGradingSystem class wrapper
# ===================================================================

class TestPAUGradingSystemClass:

    def test_class_get_letter_grade(self):
        assert PAUGradingSystem.get_letter_grade(75) == "A"

    def test_class_get_grade_point(self):
        assert PAUGradingSystem.get_grade_point(65) == 4.0

    def test_class_calculate_cgpa(self):
        courses = [
            {"grade_point": 5.0, "credits": 3},
            {"grade_point": 4.0, "credits": 3},
        ]
        assert PAUGradingSystem.calculate_cgpa(courses) == 4.5

    def test_class_get_classification(self):
        assert PAUGradingSystem.get_classification(4.5) == "First Class"

    def test_class_calculate_course_grade(self):
        result = PAUGradingSystem.calculate_course_grade(
            ca_tasks_score=25,
            participation_score=4,
            exam_score=50,
        )
        assert result["final_score"] == 79
        assert result["letter_grade"] == "A"
