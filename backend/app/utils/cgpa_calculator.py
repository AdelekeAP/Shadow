"""
CGPA Calculator - Handles all CGPA-related calculations
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.course import Course, UserCourse, Semester
from app.models.task import Task
from app.utils.pau_grading import PAUGradingSystem


class CGPACalculator:
    """Calculate CGPA based on PAU grading system"""

    @staticmethod
    def calculate_course_gpa(score: float) -> float:
        """
        Convert a course score to GPA points

        Args:
            score: Numerical score (0-100)

        Returns:
            GPA points (0.0-5.0)
        """
        return PAUGradingSystem.get_grade_point(score)

    @staticmethod
    def calculate_semester_gpa(courses: List[Dict]) -> Dict:
        """
        Calculate GPA for a semester

        Args:
            courses: List of dicts with 'credits' and 'score' keys

        Returns:
            Dict with gpa, total_credits, and quality_points
        """
        total_credits = 0
        total_quality_points = 0.0

        for course in courses:
            credits = course.get('credits', 0)
            score = course.get('score', 0)

            if score > 0:  # Only include courses with scores
                grade_point = CGPACalculator.calculate_course_gpa(score)
                quality_points = grade_point * credits

                total_credits += credits
                total_quality_points += quality_points

        gpa = total_quality_points / total_credits if total_credits > 0 else 0.0

        return {
            'gpa': round(gpa, 2),
            'total_credits': total_credits,
            'quality_points': round(total_quality_points, 2)
        }

    @staticmethod
    def calculate_cumulative_gpa(semesters: List[Dict]) -> Dict:
        """
        Calculate cumulative GPA across multiple semesters

        Args:
            semesters: List of semester dicts with 'courses' key

        Returns:
            Dict with cgpa, total_credits, and semester_breakdown
        """
        total_credits = 0
        total_quality_points = 0.0
        semester_breakdown = []

        for semester in semesters:
            semester_result = CGPACalculator.calculate_semester_gpa(
                semester.get('courses', [])
            )

            total_credits += semester_result['total_credits']
            total_quality_points += semester_result['quality_points']

            semester_breakdown.append({
                'semester': semester.get('name', 'Unknown'),
                'gpa': semester_result['gpa'],
                'credits': semester_result['total_credits']
            })

        cgpa = total_quality_points / total_credits if total_credits > 0 else 0.0

        return {
            'cgpa': round(cgpa, 2),
            'total_credits': total_credits,
            'total_quality_points': round(total_quality_points, 2),
            'semester_breakdown': semester_breakdown
        }

    @staticmethod
    def predict_final_cgpa(
        current_cgpa: float,
        current_credits: int,
        predicted_courses: List[Dict],
        remaining_semesters: int = 4
    ) -> Dict:
        """
        Predict final CGPA based on current standing and predicted performance

        Args:
            current_cgpa: Current cumulative GPA
            current_credits: Credits completed so far
            predicted_courses: List of courses with predicted scores
            remaining_semesters: Number of semesters remaining

        Returns:
            Dict with predicted_cgpa and breakdown
        """
        current_quality_points = current_cgpa * current_credits

        # Calculate quality points from predicted courses
        predicted_credits = 0
        predicted_quality_points = 0.0

        for course in predicted_courses:
            credits = course.get('credits', 0)
            predicted_score = course.get('predicted_score', 0)

            if predicted_score > 0:
                grade_point = CGPACalculator.calculate_course_gpa(predicted_score)
                predicted_quality_points += grade_point * credits
                predicted_credits += credits

        total_quality_points = current_quality_points + predicted_quality_points
        total_credits = current_credits + predicted_credits

        predicted_cgpa = total_quality_points / total_credits if total_credits > 0 else 0.0

        return {
            'predicted_cgpa': round(predicted_cgpa, 2),
            'current_cgpa': round(current_cgpa, 2),
            'credits_completed': current_credits,
            'credits_remaining': predicted_credits,
            'total_credits': total_credits
        }

    @staticmethod
    def calculate_target_semester_gpa(
        current_cgpa: float,
        current_credits: int,
        target_cgpa: float,
        semester_credits: int
    ) -> Dict:
        """
        Calculate what GPA is needed this semester to reach target CGPA

        Args:
            current_cgpa: Current cumulative GPA
            current_credits: Credits completed
            target_cgpa: Desired cumulative GPA
            semester_credits: Credits for current semester

        Returns:
            Dict with required_gpa and feasibility assessment
        """
        current_quality_points = current_cgpa * current_credits
        target_quality_points = target_cgpa * (current_credits + semester_credits)

        required_quality_points = target_quality_points - current_quality_points
        required_gpa = required_quality_points / semester_credits if semester_credits > 0 else 0.0

        # Check feasibility (max GPA is 5.0)
        is_achievable = 0.0 <= required_gpa <= 5.0
        difficulty = "Easy" if required_gpa <= 3.5 else "Moderate" if required_gpa <= 4.5 else "Challenging"

        if not is_achievable:
            if required_gpa > 5.0:
                difficulty = "Impossible - Target too high"
            else:
                difficulty = "Already exceeded target"

        return {
            'required_gpa': round(required_gpa, 2),
            'is_achievable': is_achievable,
            'difficulty': difficulty,
            'target_cgpa': target_cgpa,
            'current_cgpa': round(current_cgpa, 2)
        }

    @staticmethod
    def get_user_cgpa_data(db: Session, user_id: int) -> Dict:
        """
        Get comprehensive CGPA data for a user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Complete CGPA analysis
        """
        # Get user to access target_cgpa
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        user_target_cgpa = float(user.target_cgpa) if user and user.target_cgpa else 4.5

        # Get all user's enrolled courses
        user_courses = db.query(UserCourse).filter(UserCourse.user_id == user_id).all()

        # Group by semester (for now, use a default semester since we may not have semester data)
        semesters = {}
        for user_course in user_courses:
            # Default semester key if no semester assigned
            semester_key = "Current Semester"

            if semester_key not in semesters:
                semesters[semester_key] = {
                    'name': semester_key,
                    'courses': []
                }

            # Get course tasks to calculate current score
            tasks = db.query(Task).filter(
                Task.user_course_id == user_course.id,
                Task.earned_marks.isnot(None)
            ).all()

            total_weight = sum(task.weight for task in tasks if task.weight)
            weighted_score = sum((task.earned_marks or 0) * (task.weight / 100) for task in tasks if task.weight)

            current_score = weighted_score if total_weight > 0 else 0

            semesters[semester_key]['courses'].append({
                'id': str(user_course.id),
                'code': user_course.course.code if user_course.course else 'Unknown',
                'name': user_course.course.title if user_course.course else 'Unknown Course',
                'credits': user_course.course.credits if user_course.course else 0,
                'score': current_score,
                'grade': PAUGradingSystem.get_letter_grade(current_score) if current_score > 0 else 'N/A',
                'grade_point': CGPACalculator.calculate_course_gpa(current_score)
            })

        # Calculate cumulative GPA
        semester_list = list(semesters.values())
        cumulative_data = CGPACalculator.calculate_cumulative_gpa(semester_list)

        # Get predicted courses (courses with incomplete tasks)
        predicted_courses = []
        for user_course in user_courses:
            tasks = db.query(Task).filter(Task.user_course_id == user_course.id).all()
            completed_weight = sum(task.weight for task in tasks if task.earned_marks is not None and task.weight)

            if completed_weight < 100:  # Course not fully graded
                # Use current average for prediction
                scored_tasks = [task for task in tasks if task.earned_marks is not None]
                avg_score = sum(task.earned_marks for task in scored_tasks) / len(scored_tasks) if scored_tasks else 75.0

                predicted_courses.append({
                    'credits': user_course.course.credits if user_course.course else 0,
                    'predicted_score': avg_score
                })

        # Calculate predictions
        predicted_data = CGPACalculator.predict_final_cgpa(
            current_cgpa=cumulative_data['cgpa'],
            current_credits=cumulative_data['total_credits'],
            predicted_courses=predicted_courses
        )

        # Calculate target requirements using user's target CGPA
        # Estimate current semester credits
        current_semester_credits = sum(
            user_course.course.credits if user_course.course else 0
            for user_course in user_courses
        )

        target_gpa_data = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=cumulative_data['cgpa'],
            current_credits=cumulative_data['total_credits'],
            target_cgpa=user_target_cgpa,
            semester_credits=current_semester_credits if current_semester_credits > 0 else 18  # Default 18 credits
        )

        return {
            'current': cumulative_data,
            'predictions': predicted_data,
            'target_analysis': target_gpa_data,
            'semesters': semester_list,
            'total_courses': len(user_courses)
        }
