"""
PAU-Specific Grading System Utilities
35/65 CA/Exam Split with 5.0 Scale
"""
from typing import Dict, Tuple, Optional

# PAU Grade Scale (5.0 system)
PAU_GRADE_SCALE = {
    (70, 100): {"grade": "A", "points": 5.0, "description": "Excellent"},
    (60, 69):  {"grade": "B", "points": 4.0, "description": "Good"},
    (50, 59):  {"grade": "C", "points": 3.0, "description": "Fair"},
    (45, 49):  {"grade": "D", "points": 2.0, "description": "Pass"},
    (40, 44):  {"grade": "E", "points": 1.0, "description": "Conditional Pass"},
    (0, 39):   {"grade": "F", "points": 0.0, "description": "Fail"}
}

# Classification Thresholds
FIRST_CLASS = 4.50
SECOND_CLASS_UPPER = 3.50
SECOND_CLASS_LOWER = 2.40
THIRD_CLASS = 1.50

# Assessment Structure
CONTINUOUS_ASSESSMENT = 35  # Fixed
FINAL_EXAM = 65            # Fixed
CA_ASSESSMENTS = 30        # Tests + Projects (minimum 2)
CA_PARTICIPATION = 5       # Class engagement


def convert_score_to_grade(score: float) -> Dict[str, any]:
    """
    Convert numerical score to PAU grade information

    Args:
        score: Score out of 100

    Returns:
        Dict with grade, points, and description
    """
    for (min_score, max_score), grade_info in PAU_GRADE_SCALE.items():
        if min_score <= score <= max_score:
            return grade_info
    return {"grade": "F", "points": 0.0, "description": "Fail"}


def get_letter_grade(score: float) -> str:
    """Get letter grade from score"""
    return convert_score_to_grade(score)["grade"]


def get_grade_point(score: float) -> float:
    """Get grade point from score"""
    return convert_score_to_grade(score)["points"]


def calculate_cgpa(courses: list) -> float:
    """
    Calculate CGPA using PAU formula
    CGPA = Σ(Grade Points × Credits) / Σ(Credits)

    Args:
        courses: List of dicts with 'grade_point' and 'credits' keys

    Returns:
        CGPA (0.0 - 5.0)
    """
    if not courses:
        return 0.0

    total_grade_points = sum(
        course.get('grade_point', 0) * course.get('credits', 0)
        for course in courses
    )
    total_credits = sum(course.get('credits', 0) for course in courses)

    if total_credits == 0:
        return 0.0

    cgpa = total_grade_points / total_credits
    return round(cgpa, 2)


def get_classification(cgpa: float) -> str:
    """
    Get degree classification based on CGPA

    Args:
        cgpa: Cumulative GPA (0.0 - 5.0)

    Returns:
        Classification string
    """
    if cgpa >= FIRST_CLASS:
        return "First Class"
    elif cgpa >= SECOND_CLASS_UPPER:
        return "Second Class Upper"
    elif cgpa >= SECOND_CLASS_LOWER:
        return "Second Class Lower"
    elif cgpa >= THIRD_CLASS:
        return "Third Class"
    elif cgpa >= 1.0:
        return "Pass"
    else:
        return "Fail"


def predict_exam_score(ca_score: float, course_difficulty: float = 1.0) -> float:
    """
    Predict exam performance based on CA score

    Args:
        ca_score: CA score out of 35
        course_difficulty: Multiplier (0.8-1.2), default 1.0

    Returns:
        Predicted exam score out of 65
    """
    # Convert CA (out of 35) to percentage
    ca_percentage = ca_score / 35

    # Apply regression to mean (exams typically harder)
    exam_percentage = ca_percentage * 0.85  # 85% of CA performance

    # Adjust for course difficulty
    exam_percentage *= course_difficulty

    # Convert to exam score (out of 65)
    predicted_exam = exam_percentage * 65

    return round(predicted_exam, 2)


def estimate_participation(completion_rate: float) -> float:
    """
    Estimate participation score (5 marks) based on task completion

    Args:
        completion_rate: Task completion rate (0.0 - 1.0)

    Returns:
        Estimated participation score (0-5)
    """
    if completion_rate >= 0.85:
        return 5.0  # Full marks
    elif completion_rate >= 0.70:
        return 4.0  # Good participation
    elif completion_rate >= 0.60:
        return 3.0  # Average participation
    else:
        return 2.5  # Below average


def calculate_course_grade(
    ca_tasks_score: float,
    participation_score: Optional[float] = None,
    exam_score: Optional[float] = None,
    completion_rate: float = 0.75,
    course_difficulty: float = 1.0
) -> Dict[str, any]:
    """
    Calculate course grade using PAU's 35/65 split

    Args:
        ca_tasks_score: Sum of CA tasks (out of 30)
        participation_score: Participation score (out of 5), estimated if None
        exam_score: Exam score (out of 65), predicted if None
        completion_rate: Task completion rate for participation estimation
        course_difficulty: Course difficulty multiplier

    Returns:
        Dict with ca_score, exam_score, final_score, grade_point, letter_grade
    """
    # Handle participation
    if participation_score is None:
        participation_score = estimate_participation(completion_rate)

    # Total CA (out of 35)
    total_ca = ca_tasks_score + participation_score
    total_ca = min(total_ca, 35)  # Cap at 35

    # Handle exam
    if exam_score is None:
        exam_score = predict_exam_score(total_ca, course_difficulty)

    # Final score (out of 100)
    final_score = total_ca + exam_score
    final_score = min(final_score, 100)  # Cap at 100

    # Convert to grade
    grade_info = convert_score_to_grade(final_score)

    return {
        "ca_score": round(total_ca, 2),
        "exam_score": round(exam_score, 2),
        "final_score": round(final_score, 2),
        "grade_point": grade_info["points"],
        "letter_grade": grade_info["grade"],
        "description": grade_info["description"],
        "is_predicted": exam_score is not None and participation_score is None
    }


def validate_ca_allocation(tasks: list) -> Dict[str, any]:
    """
    Validate that CA tasks don't exceed 30 marks

    Args:
        tasks: List of tasks with 'weight' values

    Returns:
        Dict with is_valid, total_allocated, remaining
    """
    total_allocated = sum(task.get('weight', 0) for task in tasks if task.get('category') == 'CA')
    remaining = CA_ASSESSMENTS - total_allocated

    return {
        "is_valid": total_allocated <= CA_ASSESSMENTS,
        "total_allocated": round(total_allocated, 2),
        "remaining": round(remaining, 2),
        "max_ca": CA_ASSESSMENTS,
        "participation": CA_PARTICIPATION
    }


# Class-based API for convenience
class PAUGradingSystem:
    """PAU Grading System - Class-based wrapper for functional utilities"""

    @staticmethod
    def get_letter_grade(score: float) -> str:
        """Get letter grade from score"""
        return get_letter_grade(score)

    @staticmethod
    def get_grade_point(score: float) -> float:
        """Get grade point from score"""
        return get_grade_point(score)

    @staticmethod
    def calculate_cgpa(courses: list) -> float:
        """Calculate CGPA"""
        return calculate_cgpa(courses)

    @staticmethod
    def get_classification(cgpa: float) -> str:
        """Get degree classification"""
        return get_classification(cgpa)

    @staticmethod
    def calculate_course_grade(
        ca_tasks_score: float,
        participation_score: Optional[float] = None,
        exam_score: Optional[float] = None,
        completion_rate: float = 0.75,
        course_difficulty: float = 1.0
    ) -> Dict[str, any]:
        """Calculate course grade"""
        return calculate_course_grade(
            ca_tasks_score,
            participation_score,
            exam_score,
            completion_rate,
            course_difficulty
        )
