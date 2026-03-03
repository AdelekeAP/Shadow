"""
Tests for Legacy Grading Utilities
backend/app/utils/grading.py

This is the original grading module (uses tuples instead of dicts).
Tests ensure backward compatibility with any code still using these functions.
"""
import pytest
from app.utils.grading import (
    convert_to_grade_point,
    predict_exam_score,
    calculate_predicted_grade,
    calculate_cgpa,
    calculate_semester_gpa,
    get_grade_recommendation,
)


# ===================================================================
# convert_to_grade_point
# ===================================================================

class TestConvertToGradePoint:

    def test_A_grade(self):
        letter, points = convert_to_grade_point(75)
        assert letter == "A"
        assert points == 5.0

    def test_B_grade(self):
        letter, points = convert_to_grade_point(65)
        assert letter == "B"
        assert points == 4.0

    def test_C_grade(self):
        letter, points = convert_to_grade_point(55)
        assert letter == "C"
        assert points == 3.0

    def test_D_grade(self):
        letter, points = convert_to_grade_point(47)
        assert letter == "D"
        assert points == 2.0

    def test_E_grade(self):
        letter, points = convert_to_grade_point(42)
        assert letter == "E"
        assert points == 1.0

    def test_F_grade(self):
        letter, points = convert_to_grade_point(20)
        assert letter == "F"
        assert points == 0.0

    def test_boundary_70(self):
        letter, _ = convert_to_grade_point(70)
        assert letter == "A"

    def test_boundary_69(self):
        letter, _ = convert_to_grade_point(69)
        assert letter == "B"

    def test_boundary_40(self):
        letter, _ = convert_to_grade_point(40)
        assert letter == "E"

    def test_boundary_39(self):
        letter, _ = convert_to_grade_point(39)
        assert letter == "F"

    def test_invalid_negative_score(self):
        letter, points = convert_to_grade_point(-5)
        assert letter == "F"
        assert points == 0.0


# ===================================================================
# predict_exam_score (legacy version - uses /30 not /35)
# ===================================================================

class TestLegacyPredictExamScore:

    def test_full_ca_score(self):
        # 30/30 → 1.0 → 0.85 → 0.85*65 = 55.25
        result = predict_exam_score(30)
        assert result == 55.25

    def test_zero_ca(self):
        assert predict_exam_score(0) == 0.0

    def test_half_ca(self):
        # 15/30 → 0.5 → 0.425 → 27.625 → 27.62
        result = predict_exam_score(15)
        assert result == 27.62

    def test_high_difficulty(self):
        # 30/30 → 1.0 → 0.85*1.2=1.02 → capped at 1.0 → 65.0
        result = predict_exam_score(30, course_difficulty=1.2)
        assert result == 65.0  # Capped at 100%

    def test_low_difficulty(self):
        # 30/30 → 1.0 → 0.85*0.8=0.68 → 44.2
        result = predict_exam_score(30, course_difficulty=0.8)
        assert result == 44.2


# ===================================================================
# calculate_predicted_grade
# ===================================================================

class TestCalculatePredictedGrade:

    def test_with_exam_score(self):
        current, predicted, letter, gp = calculate_predicted_grade(
            ca_score=30, exam_score=50
        )
        assert current == 80  # 30+50
        assert predicted == 80  # Same when exam is known
        assert letter == "A"
        assert gp == 5.0

    def test_without_exam_score(self):
        current, predicted, letter, gp = calculate_predicted_grade(ca_score=25)
        assert current == 25  # Only CA so far
        assert predicted > 25  # Should have predicted exam added

    def test_low_ca_predicts_lower(self):
        _, predicted_high, _, _ = calculate_predicted_grade(ca_score=28)
        _, predicted_low, _, _ = calculate_predicted_grade(ca_score=10)
        assert predicted_high > predicted_low


# ===================================================================
# calculate_cgpa (legacy tuple-based version)
# ===================================================================

class TestLegacyCalculateCGPA:

    def test_basic_cgpa(self):
        grade_points = [(5.0, 3), (4.0, 3), (3.0, 2)]
        # (15+12+6) / (3+3+2) = 33/8 = 4.12
        result = calculate_cgpa(grade_points)
        assert result == 4.12

    def test_all_A(self):
        grade_points = [(5.0, 3), (5.0, 3), (5.0, 3)]
        assert calculate_cgpa(grade_points) == 5.0

    def test_empty_list(self):
        assert calculate_cgpa([]) == 0.0

    def test_zero_credits(self):
        grade_points = [(5.0, 0)]
        assert calculate_cgpa(grade_points) == 0.0


# ===================================================================
# calculate_semester_gpa
# ===================================================================

class TestLegacySemesterGPA:

    def test_basic_semester(self):
        courses = [
            {"grade_point": 5.0, "credits": 3},
            {"grade_point": 4.0, "credits": 3},
        ]
        # (15+12)/6 = 4.5
        result = calculate_semester_gpa(courses)
        assert result == 4.5

    def test_excludes_none_grade_points(self):
        courses = [
            {"grade_point": 5.0, "credits": 3},
            {"grade_point": None, "credits": 3},
        ]
        result = calculate_semester_gpa(courses)
        assert result == 5.0


# ===================================================================
# get_grade_recommendation
# ===================================================================

class TestGetGradeRecommendation:

    def test_on_track(self):
        result = get_grade_recommendation(
            current_cgpa=4.5,
            target_cgpa=4.0,
            ca_score=30,
            predicted_grade_point=5.0,
        )
        assert result["status"] == "excellent"

    def test_needs_improvement(self):
        result = get_grade_recommendation(
            current_cgpa=3.0,
            target_cgpa=4.5,
            ca_score=15,
            predicted_grade_point=2.5,
        )
        assert result["status"] == "needs_improvement"
        assert len(result["suggestions"]) > 0

    def test_at_risk(self):
        result = get_grade_recommendation(
            current_cgpa=2.0,
            target_cgpa=4.0,
            ca_score=10,
            predicted_grade_point=1.5,
        )
        assert result["status"] == "at_risk"
        assert "immediate attention" in result["message"]
        assert any("study time" in s for s in result["suggestions"])

    def test_good_performance(self):
        result = get_grade_recommendation(
            current_cgpa=4.0,
            target_cgpa=4.0,
            ca_score=25,
            predicted_grade_point=4.0,
        )
        assert result["status"] == "good"

    def test_low_ca_gets_suggestion(self):
        result = get_grade_recommendation(
            current_cgpa=4.0,
            target_cgpa=4.0,
            ca_score=15,  # 15/35 = 42.8% < 60%
            predicted_grade_point=3.5,
        )
        assert any("CA score" in s for s in result["suggestions"])
