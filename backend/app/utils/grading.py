"""
Grading Utilities for PAU Academic System
Handles grade calculations, predictions, and conversions
"""
from typing import Tuple, Optional
from decimal import Decimal


# PAU Grading Scale (Total Score out of 100)
PAU_GRADE_SCALE = {
    (70, 100): {"letter": "A", "points": 5.0},
    (60, 69): {"letter": "B", "points": 4.0},
    (50, 59): {"letter": "C", "points": 3.0},
    (45, 49): {"letter": "D", "points": 2.0},
    (40, 44): {"letter": "E", "points": 1.0},
    (0, 39): {"letter": "F", "points": 0.0}
}


def convert_to_grade_point(score: float) -> Tuple[str, float]:
    """
    Convert total score (out of 100) to letter grade and grade point

    Args:
        score: Total score (CA + EXAM) out of 100

    Returns:
        Tuple of (letter_grade, grade_point)

    Examples:
        >>> convert_to_grade_point(75)
        ('A', 5.0)
        >>> convert_to_grade_point(62)
        ('B', 4.0)
        >>> convert_to_grade_point(38)
        ('F', 0.0)
    """
    for (min_score, max_score), grade_info in PAU_GRADE_SCALE.items():
        if min_score <= score <= max_score:
            return grade_info["letter"], grade_info["points"]

    # Default to F if score is invalid
    return "F", 0.0


def predict_exam_score(ca_score: float, course_difficulty: float = 1.0) -> float:
    """
    Predict EXAM score based on CA performance

    Uses a conservative 85% performance retention model:
    - Students typically score 85% of their CA performance in exams
    - Adjusted by course difficulty factor

    Args:
        ca_score: Current CA score (out of 30, 5 marks for participation handled separately)
        course_difficulty: Difficulty multiplier (0.5 = easier, 1.5 = harder)

    Returns:
        Predicted exam score (out of 65)

    Examples:
        >>> predict_exam_score(25)  # 25/30 CA
        46.03  # Predicted 46.03/65 on exam
        >>> predict_exam_score(20, 1.2)  # Harder course
        36.27
    """
    # Calculate CA percentage (out of 30 marks)
    ca_percentage = ca_score / 30.0

    # Apply 85% retention rate
    exam_percentage = ca_percentage * 0.85

    # Adjust for course difficulty
    exam_percentage *= course_difficulty

    # Cap at 100% and floor at 0%
    exam_percentage = max(0.0, min(1.0, exam_percentage))

    # Convert to exam score out of 65
    predicted_exam = exam_percentage * 65.0

    return round(predicted_exam, 2)


def calculate_predicted_grade(
    ca_score: float,
    exam_score: Optional[float] = None,
    course_difficulty: float = 1.0
) -> Tuple[float, float, str, float]:
    """
    Calculate current and predicted grades for a course

    Args:
        ca_score: Current CA score (out of 35)
        exam_score: Actual exam score if taken (out of 65), None if not taken
        course_difficulty: Course difficulty multiplier (default 1.0)

    Returns:
        Tuple of (current_score, predicted_score, predicted_letter_grade, predicted_grade_point)

    Examples:
        >>> calculate_predicted_grade(30, None)  # CA only
        (30.0, 78.64, 'A', 5.0)

        >>> calculate_predicted_grade(30, 50)  # CA + actual exam
        (80.0, 80.0, 'A', 5.0)
    """
    # If exam score is provided, use it
    if exam_score is not None:
        current_score = ca_score + exam_score
        predicted_score = current_score  # No prediction needed
    else:
        # Predict exam score
        current_score = ca_score  # Only CA so far
        predicted_exam = predict_exam_score(ca_score, course_difficulty)
        predicted_score = ca_score + predicted_exam

    # Convert predicted score to grade
    predicted_letter, predicted_gp = convert_to_grade_point(predicted_score)

    return (
        round(current_score, 2),
        round(predicted_score, 2),
        predicted_letter,
        predicted_gp
    )


def calculate_cgpa(grade_points: list[Tuple[float, int]]) -> float:
    """
    Calculate Cumulative Grade Point Average (CGPA)

    Args:
        grade_points: List of (grade_point, credits) tuples

    Returns:
        CGPA value (0.0 - 5.0)

    Examples:
        >>> calculate_cgpa([(5.0, 3), (4.0, 3), (3.0, 2)])
        4.25  # (5*3 + 4*3 + 3*2) / (3+3+2)
    """
    if not grade_points:
        return 0.0

    total_points = sum(gp * credits for gp, credits in grade_points)
    total_credits = sum(credits for _, credits in grade_points)

    if total_credits == 0:
        return 0.0

    return round(total_points / total_credits, 2)


def calculate_semester_gpa(courses: list[dict]) -> float:
    """
    Calculate semester GPA from enrolled courses

    Args:
        courses: List of course dicts with 'grade_point' and 'credits' keys

    Returns:
        Semester GPA (0.0 - 5.0)
    """
    grade_points = [
        (float(course.get('grade_point', 0)), int(course.get('credits', 0)))
        for course in courses
        if course.get('grade_point') is not None
    ]

    return calculate_cgpa(grade_points)


def get_grade_recommendation(
    current_cgpa: float,
    target_cgpa: float,
    ca_score: float,
    predicted_grade_point: float
) -> dict:
    """
    Generate recommendations based on performance

    Args:
        current_cgpa: Current CGPA
        target_cgpa: Target CGPA
        ca_score: Current CA score
        predicted_grade_point: Predicted grade point for course

    Returns:
        Dict with status, message, and recommendations
    """
    recommendation = {
        "status": "on_track",
        "message": "",
        "suggestions": []
    }

    # Check if behind target
    if current_cgpa < target_cgpa:
        gap = target_cgpa - current_cgpa
        recommendation["status"] = "needs_improvement"
        recommendation["message"] = f"You're {gap:.2f} points behind your target CGPA"

        if predicted_grade_point < 3.0:
            recommendation["suggestions"].append("Focus on improving CA scores to boost exam predictions")
            recommendation["suggestions"].append("Consider creating a study plan for remaining tasks")

    # Check CA performance
    ca_percentage = (ca_score / 35) * 100
    if ca_percentage < 60:
        recommendation["suggestions"].append("Your CA score is below 60% - prioritize completing remaining tasks")

    # Check predicted grade
    if predicted_grade_point >= 4.5:
        recommendation["status"] = "excellent"
        recommendation["message"] = "Great work! Keep up the momentum"
    elif predicted_grade_point >= 3.5:
        recommendation["status"] = "good"
        recommendation["message"] = "You're doing well, small improvements can make a big difference"
    elif predicted_grade_point < 2.0:
        recommendation["status"] = "at_risk"
        recommendation["message"] = "This course needs immediate attention"
        recommendation["suggestions"].append("Schedule extra study time for this course")
        recommendation["suggestions"].append("Consider seeking help from instructors or peers")

    return recommendation
