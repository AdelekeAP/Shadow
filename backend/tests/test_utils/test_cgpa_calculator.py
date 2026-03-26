"""
Tests for CGPA Calculator
backend/app/utils/cgpa_calculator.py

Tests the pure calculation methods that don't require a database connection.
The DB-dependent get_user_cgpa_data is tested separately in integration tests.
"""
import pytest
from app.utils.cgpa_calculator import CGPACalculator


# ===================================================================
# calculate_course_gpa
# ===================================================================

class TestCalculateCourseGPA:

    def test_score_100_gives_5_0(self):
        assert CGPACalculator.calculate_course_gpa(100) == 5.0

    def test_score_70_gives_5_0(self):
        assert CGPACalculator.calculate_course_gpa(70) == 5.0

    def test_score_65_gives_4_0(self):
        assert CGPACalculator.calculate_course_gpa(65) == 4.0

    def test_score_55_gives_3_0(self):
        assert CGPACalculator.calculate_course_gpa(55) == 3.0

    def test_score_47_gives_2_0(self):
        assert CGPACalculator.calculate_course_gpa(47) == 2.0

    def test_score_42_gives_1_0(self):
        assert CGPACalculator.calculate_course_gpa(42) == 1.0

    def test_score_30_gives_0_0(self):
        assert CGPACalculator.calculate_course_gpa(30) == 0.0

    def test_score_0_gives_0_0(self):
        assert CGPACalculator.calculate_course_gpa(0) == 0.0


# ===================================================================
# calculate_semester_gpa
# ===================================================================

class TestCalculateSemesterGPA:

    def test_single_course(self):
        courses = [{"credits": 3, "score": 75}]
        result = CGPACalculator.calculate_semester_gpa(courses)
        assert result["gpa"] == 5.0  # 75 → A → 5.0
        assert result["total_credits"] == 3
        assert result["quality_points"] == 15.0

    def test_multiple_courses(self):
        courses = [
            {"credits": 3, "score": 75},  # A → 5.0 → QP=15
            {"credits": 3, "score": 65},  # B → 4.0 → QP=12
            {"credits": 3, "score": 55},  # C → 3.0 → QP=9
        ]
        result = CGPACalculator.calculate_semester_gpa(courses)
        # Total QP = 36, Total Credits = 9, GPA = 36/9 = 4.0
        assert result["gpa"] == 4.0
        assert result["total_credits"] == 9
        assert result["quality_points"] == 36.0

    def test_courses_with_zero_scores_included_as_F(self):
        courses = [
            {"credits": 3, "score": 75},  # A = 5.0, QP = 15
            {"credits": 3, "score": 0},   # F = 0.0, QP = 0
        ]
        result = CGPACalculator.calculate_semester_gpa(courses)
        assert result["gpa"] == 2.5  # 15 / 6
        assert result["total_credits"] == 6

    def test_empty_courses(self):
        result = CGPACalculator.calculate_semester_gpa([])
        assert result["gpa"] == 0.0
        assert result["total_credits"] == 0

    def test_all_A_grades(self):
        courses = [
            {"credits": 3, "score": 80},
            {"credits": 3, "score": 90},
            {"credits": 3, "score": 70},
        ]
        result = CGPACalculator.calculate_semester_gpa(courses)
        assert result["gpa"] == 5.0

    def test_all_F_grades(self):
        courses = [
            {"credits": 3, "score": 20},
            {"credits": 3, "score": 10},
        ]
        result = CGPACalculator.calculate_semester_gpa(courses)
        assert result["gpa"] == 0.0

    def test_realistic_mixed_semester(self):
        """Realistic PAU 400L semester"""
        courses = [
            {"credits": 3, "score": 72},   # A → 5.0
            {"credits": 3, "score": 63},   # B → 4.0
            {"credits": 3, "score": 58},   # C → 3.0
            {"credits": 3, "score": 71},   # A → 5.0
            {"credits": 2, "score": 67},   # B → 4.0
            {"credits": 4, "score": 54},   # C → 3.0
        ]
        # QP: 15+12+9+15+8+12 = 71
        # Credits: 3+3+3+3+2+4 = 18
        # GPA: 71/18 = 3.94
        result = CGPACalculator.calculate_semester_gpa(courses)
        assert result["gpa"] == 3.94
        assert result["total_credits"] == 18


# ===================================================================
# calculate_cumulative_gpa
# ===================================================================

class TestCalculateCumulativeGPA:

    def test_single_semester(self):
        semesters = [{
            "name": "Semester 1",
            "courses": [
                {"credits": 3, "score": 75},
                {"credits": 3, "score": 65},
            ],
        }]
        result = CGPACalculator.calculate_cumulative_gpa(semesters)
        # QP: 15+12=27, Credits: 6, CGPA: 4.5
        assert result["cgpa"] == 4.5
        assert result["total_credits"] == 6
        assert len(result["semester_breakdown"]) == 1

    def test_two_semesters(self):
        semesters = [
            {
                "name": "Semester 1",
                "courses": [
                    {"credits": 3, "score": 75},  # A → 15 QP
                    {"credits": 3, "score": 75},  # A → 15 QP
                ],
            },
            {
                "name": "Semester 2",
                "courses": [
                    {"credits": 3, "score": 55},  # C → 9 QP
                    {"credits": 3, "score": 55},  # C → 9 QP
                ],
            },
        ]
        result = CGPACalculator.calculate_cumulative_gpa(semesters)
        # Total QP: 30+18=48, Credits: 12, CGPA: 48/12 = 4.0
        assert result["cgpa"] == 4.0
        assert result["total_credits"] == 12
        assert len(result["semester_breakdown"]) == 2

    def test_empty_semesters(self):
        result = CGPACalculator.calculate_cumulative_gpa([])
        assert result["cgpa"] == 0.0
        assert result["total_credits"] == 0


# ===================================================================
# predict_final_cgpa
# ===================================================================

class TestPredictFinalCGPA:

    def test_basic_prediction(self):
        result = CGPACalculator.predict_final_cgpa(
            current_cgpa=4.0,
            current_credits=60,
            predicted_courses=[
                {"credits": 3, "predicted_score": 75},  # A → 5.0
                {"credits": 3, "predicted_score": 65},  # B → 4.0
            ],
        )
        # Current QP = 4.0*60=240
        # Predicted QP = 15+12=27
        # Total: 267/66 = 4.05
        assert result["predicted_cgpa"] == 4.05
        assert result["credits_completed"] == 60
        assert result["credits_remaining"] == 6
        assert result["total_credits"] == 66

    def test_no_predicted_courses(self):
        result = CGPACalculator.predict_final_cgpa(
            current_cgpa=3.5,
            current_credits=30,
            predicted_courses=[],
        )
        assert result["predicted_cgpa"] == 3.5
        assert result["credits_remaining"] == 0

    def test_prediction_with_zero_scores_excluded(self):
        result = CGPACalculator.predict_final_cgpa(
            current_cgpa=4.0,
            current_credits=60,
            predicted_courses=[
                {"credits": 3, "predicted_score": 0},   # Excluded
                {"credits": 3, "predicted_score": 75},   # Included
            ],
        )
        # Only 1 course: QP=15, Credits=3
        # Total: (240+15)/63 = 4.05
        assert result["predicted_cgpa"] == 4.05

    def test_prediction_improves_cgpa(self):
        """All A's should improve a lower CGPA"""
        result = CGPACalculator.predict_final_cgpa(
            current_cgpa=3.0,
            current_credits=60,
            predicted_courses=[
                {"credits": 3, "predicted_score": 80},  # A
                {"credits": 3, "predicted_score": 80},  # A
                {"credits": 3, "predicted_score": 80},  # A
                {"credits": 3, "predicted_score": 80},  # A
                {"credits": 3, "predicted_score": 80},  # A
                {"credits": 3, "predicted_score": 80},  # A
            ],
        )
        assert result["predicted_cgpa"] > 3.0


# ===================================================================
# calculate_target_semester_gpa
# ===================================================================

class TestCalculateTargetSemesterGPA:

    def test_achievable_target(self):
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=3.5,
            current_credits=60,
            target_cgpa=4.0,
            semester_credits=18,
        )
        # Required QP = 4.0*78 - 3.5*60 = 312 - 210 = 102
        # Required GPA = 102/18 = 5.67 → NOT achievable (>5.0)
        assert result["is_achievable"] is False
        assert result["target_cgpa"] == 4.0

    def test_easily_achievable(self):
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=4.5,
            current_credits=60,
            target_cgpa=4.0,
            semester_credits=18,
        )
        # Already exceeding target → required GPA < current
        assert result["is_achievable"] is True

    def test_already_exceeded_target(self):
        """When current CGPA is so far above target that required GPA goes negative"""
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=4.5,
            current_credits=60,
            target_cgpa=3.0,
            semester_credits=18,
        )
        # (3.0*78 - 4.5*60)/18 = (234-270)/18 = -2.0 → negative → not achievable
        assert result["is_achievable"] is False
        assert result["difficulty"] == "Already exceeded target"

    def test_impossible_target(self):
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=2.0,
            current_credits=60,
            target_cgpa=4.5,
            semester_credits=18,
        )
        # (4.5*78 - 2.0*60)/18 = (351-120)/18 = 12.83 → impossible
        assert result["is_achievable"] is False
        assert "Impossible" in result["difficulty"]

    def test_zero_semester_credits(self):
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=3.5,
            current_credits=60,
            target_cgpa=4.0,
            semester_credits=0,
        )
        assert result["required_gpa"] == 0.0

    def test_moderate_difficulty(self):
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=3.8,
            current_credits=60,
            target_cgpa=4.0,
            semester_credits=18,
        )
        # (4.0*78 - 3.8*60)/18 = (312-228)/18 = 84/18 = 4.67
        assert result["required_gpa"] == 4.67
        assert result["is_achievable"] is True
        assert result["difficulty"] == "Challenging"

    def test_easy_difficulty(self):
        result = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=4.3,
            current_credits=60,
            target_cgpa=4.0,
            semester_credits=18,
        )
        # (4.0*78 - 4.3*60)/18 = (312-258)/18 = 54/18 = 3.0
        assert result["required_gpa"] == 3.0
        assert result["difficulty"] == "Easy"
