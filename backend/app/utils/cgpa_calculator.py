"""
CGPA Calculator - Handles all CGPA-related calculations
"""
import math
from collections import defaultdict
from typing import List, Dict, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.course import Course, UserCourse, Semester
from app.models.task import Task
from app.utils.pau_grading import PAUGradingSystem, is_single_grade


def expected_score_from_cgpa(cgpa: float) -> float:
    """Project an expected course score (out of 100) from a student's CGPA.

    Used to forecast a not-yet-graded single-grade course (e.g. FYP) for the
    PREDICTED final CGPA: a student performing at a given CGPA is assumed to
    achieve a representative score in the matching grade band. Keeps the
    forecast personalised rather than a flat guess.
    """
    if cgpa >= 4.5:
        return 85.0   # A band
    if cgpa >= 3.5:
        return 65.0   # B band
    if cgpa >= 2.4:
        return 55.0   # C band
    if cgpa >= 1.5:
        return 47.0   # D band
    if cgpa >= 1.0:
        return 42.0   # E band
    return 35.0


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

        Raises:
            ValueError: If score is not in [0, 100]
        """
        score = float(score)
        if not math.isfinite(score) or score < 0 or score > 100:
            raise ValueError(f"Score must be between 0 and 100, got {score}")
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
            credits = int(course.get('credits', 0))
            score = float(course.get('score', 0))

            if credits < 0:
                credits = 0
            if not math.isfinite(score) or score < 0 or score > 100:
                raise ValueError(f"Score must be between 0 and 100, got {score}")

            if credits > 0 and score is not None:  # Include all courses with valid credits (score 0 = grade F)
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
        current_cgpa = max(min(float(current_cgpa), 5.0), 0.0)
        current_credits = max(int(current_credits), 0)
        current_quality_points = current_cgpa * current_credits

        # Calculate quality points from predicted courses
        predicted_credits = 0
        predicted_quality_points = 0.0

        for course in predicted_courses:
            credits = max(int(course.get('credits', 0)), 0)
            predicted_score = max(min(float(course.get('predicted_score', 0)), 100), 0)

            if predicted_score > 0 and credits > 0:
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
        current_cgpa = max(min(float(current_cgpa), 5.0), 0.0)
        current_credits = max(int(current_credits), 0)
        target_cgpa = max(min(float(target_cgpa), 5.0), 0.0)
        semester_credits = max(int(semester_credits), 0)

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

        # Get all user's enrolled courses with semester and course data (eager-loaded)
        user_courses = db.query(UserCourse).options(
            joinedload(UserCourse.semester),
            joinedload(UserCourse.course)
        ).filter(UserCourse.user_id == user_id).all()

        # Batch-fetch ALL tasks for this user's courses (fixes N+1 query)
        user_course_ids = [uc.id for uc in user_courses]
        all_tasks = db.query(Task).filter(
            Task.user_course_id.in_(user_course_ids)
        ).all() if user_course_ids else []

        # Group tasks by user_course_id
        tasks_by_course = defaultdict(list)
        for task in all_tasks:
            tasks_by_course[task.user_course_id].append(task)

        # Group by actual semester (using semester_id FK)
        semesters = {}
        semester_order = {}  # track start_date for sorting
        for user_course in user_courses:
            if user_course.semester_id and user_course.semester:
                semester_key = str(user_course.semester_id)
                semester_name = user_course.semester.name
                semester_order[semester_key] = user_course.semester.start_date
            else:
                semester_key = "unassigned"
                semester_name = "Current Semester"
                semester_order[semester_key] = None

            if semester_key not in semesters:
                semesters[semester_key] = {
                    'name': semester_name,
                    'courses': []
                }

            # Single-grade courses (e.g. FYP): score is the single submitted grade
            # out of 100 (stored in exam_score), not derived from tasks.
            uc_course = user_course.course
            if uc_course and is_single_grade(uc_course.grading_type, uc_course.code):
                # Pending FYP (not graded yet) is EXCLUDED from current/actual CGPA
                # — it must not be counted as an F. It's projected separately below
                # for the predicted final CGPA.
                if user_course.exam_score is None and user_course.current_score is None:
                    continue
                current_score = (
                    float(user_course.exam_score)
                    if user_course.exam_score is not None
                    else float(user_course.current_score)
                )
            else:
                # Use pre-fetched tasks (scored only for GPA calculation)
                course_tasks = tasks_by_course.get(user_course.id, [])
                scored_tasks = [
                    t for t in course_tasks
                    if t.earned_marks is not None and t.weight and (t.max_marks or t.weight)
                ]

                # No CA recorded yet → treat as "not yet assessed" and EXCLUDE from
                # current CGPA rather than scoring it 0. Mirrors pending-FYP handling.
                # (Sparse-data users are not penalised for courses they haven't logged.)
                if not scored_tasks:
                    continue

                total_weight = sum(float(t.weight) for t in scored_tasks)
                weighted_score = sum(
                    (float(t.earned_marks if t.earned_marks is not None else 0) / float(t.max_marks if t.max_marks else t.weight))
                    * float(t.weight)
                    for t in scored_tasks
                )

                current_score = (weighted_score / total_weight) * 100 if total_weight > 0 else 0

            credits = user_course.course.credits if user_course.course else 0
            semesters[semester_key]['courses'].append({
                'id': str(user_course.id),
                'code': user_course.course.code if user_course.course else 'Unknown',
                'name': user_course.course.title if user_course.course else 'Unknown Course',
                'credits': max(credits, 0),
                'score': max(min(current_score, 100), 0),
                'grade': PAUGradingSystem.get_letter_grade(current_score) if current_score is not None else 'N/A',
                'grade_point': CGPACalculator.calculate_course_gpa(current_score)
            })

        # Sort semesters chronologically (by start_date, unassigned last)
        def _sort_key(key):
            dt = semester_order.get(key)
            if dt is None:
                return (1, "")  # unassigned goes last
            return (0, dt.isoformat() if hasattr(dt, 'isoformat') else str(dt))

        sorted_keys = sorted(semesters.keys(), key=_sort_key)
        semester_list = [semesters[k] for k in sorted_keys]
        cumulative_data = CGPACalculator.calculate_cumulative_gpa(semester_list)

        # ── True cumulative CGPA ─────────────────────────────────────────────
        # `cumulative_data` above is only THIS SEMESTER's GPA (from current CA
        # performance on the enrolled courses). Blend it with the student's stored
        # historical standing so the headline figure is a true cumulative CGPA,
        # not a single-semester snapshot:
        #   true = (hist_cgpa*hist_credits + sem_gp*sem_credits) / (hist_credits + sem_credits)
        # NOTE: this semester's credits are layered ON TOP of total_credits_completed,
        # which is assumed to hold prior (pre-this-semester) credits.
        semester_gp = cumulative_data['cgpa']
        semester_credits = cumulative_data['total_credits']
        hist_cgpa = float(user.current_cgpa) if user and user.current_cgpa else None
        hist_credits = int(user.total_credits_completed or 0) if user else 0
        has_history = hist_cgpa is not None and hist_credits > 0
        if has_history:
            denom = hist_credits + semester_credits
            true_cgpa = round((hist_cgpa * hist_credits + semester_gp * semester_credits) / denom, 2) if denom > 0 else hist_cgpa
            true_credits = denom
        else:
            true_cgpa = semester_gp
            true_credits = semester_credits
        # Forecasting / feasibility baseline = prior standing; this semester is
        # layered on top via predicted_courses / the required-GPA computation.
        base_cgpa = hist_cgpa if has_history else semester_gp
        base_credits = hist_credits if has_history else semester_credits

        # Get predicted courses using pre-fetched tasks (no extra queries)
        predicted_courses = []
        for user_course in user_courses:
            # Single-grade courses (e.g. FYP): use the submitted grade if awarded,
            # otherwise (pending) project it from the student's current CGPA so the
            # final-CGPA forecast still accounts for the course's credits.
            uc_course = user_course.course
            if uc_course and is_single_grade(uc_course.grading_type, uc_course.code):
                if user_course.exam_score is not None:
                    projected = max(min(float(user_course.exam_score), 100), 0)
                else:
                    projected = expected_score_from_cgpa(true_cgpa)
                predicted_courses.append({
                    'credits': uc_course.credits if uc_course else 0,
                    'predicted_score': projected
                })
                continue

            course_tasks = tasks_by_course.get(user_course.id, [])
            completed_weight = sum(
                float(t.weight) for t in course_tasks
                if t.earned_marks is not None and t.weight
            )

            if completed_weight < 100:  # Course not fully graded
                scored = [
                    t for t in course_tasks
                    if t.earned_marks is not None and (t.max_marks or t.weight)
                ]
                avg_score = (
                    sum(
                        float(t.earned_marks) / float(t.max_marks or t.weight or 1) * 100
                        for t in scored
                    ) / len(scored)
                    if scored else 75.0
                )

                predicted_courses.append({
                    'credits': user_course.course.credits if user_course.course else 0,
                    'predicted_score': max(min(avg_score, 100), 0)
                })

        # Calculate predictions — baseline is prior standing, this semester's
        # predicted courses are added on top (true predicted cumulative CGPA).
        predicted_data = CGPACalculator.predict_final_cgpa(
            current_cgpa=base_cgpa,
            current_credits=base_credits,
            predicted_courses=predicted_courses
        )

        # Calculate target requirements using user's target CGPA
        # Only count credits from active semester or unassigned courses
        active_semester = db.query(Semester).filter(
            Semester.user_id == user_id,
            Semester.is_active == True
        ).first()

        current_semester_credits = sum(
            user_course.course.credits if user_course.course else 0
            for user_course in user_courses
            if (active_semester and user_course.semester_id == active_semester.id)
            or user_course.semester_id is None
        )

        # If no active semester credits, use historical average instead of magic number
        if current_semester_credits == 0 and semester_list:
            sem_credit_totals = []
            for sem in semester_list:
                sem_credits = sum(c.get('credits', 0) for c in sem.get('courses', []))
                if sem_credits > 0:
                    sem_credit_totals.append(sem_credits)
            if sem_credit_totals:
                current_semester_credits = round(sum(sem_credit_totals) / len(sem_credit_totals))

        # Feasibility uses the historical baseline + this semester's credits as the
        # lever, so an unreachable target (e.g. 132cr @ 3.60 needing 4.00) is
        # correctly flagged impossible even with a perfect remaining semester.
        target_gpa_data = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=base_cgpa,
            current_credits=base_credits,
            target_cgpa=user_target_cgpa,
            semester_credits=current_semester_credits if current_semester_credits > 0 else 18
        )

        # Headline 'current' figure = blended true cumulative CGPA; the raw
        # this-semester GPA is exposed separately for transparency.
        current_block = dict(cumulative_data)
        current_block.update({
            'cgpa': true_cgpa,
            'total_credits': true_credits,
            'semester_gpa': semester_gp,
            'semester_credits': semester_credits,
            'historical_cgpa': hist_cgpa,
            'historical_credits': hist_credits,
            'classification': PAUGradingSystem.get_classification(true_cgpa),
        })

        return {
            'current': current_block,
            'predictions': predicted_data,
            'target_analysis': target_gpa_data,
            'semesters': semester_list,
            'total_courses': len(user_courses)
        }
