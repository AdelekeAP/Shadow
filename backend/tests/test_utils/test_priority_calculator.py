"""
Tests for Priority Calculator
backend/app/utils/priority_calculator.py

Tests urgency scoring, weight impact scoring, mood scoring,
goal impact scoring, full priority calculation, and recommendation types.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock
from tests.conftest import MockTask, MockUser, MockMoodLog


# ===================================================================
# Urgency scoring (no DB dependency)
# ===================================================================

class TestCalculateUrgencyScore:

    def _get_calculator(self):
        from app.utils.priority_calculator import PriorityCalculator
        return PriorityCalculator

    def test_overdue_task_returns_10(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) - timedelta(days=3))
        assert calc.calculate_urgency_score(task) == 10.0

    def test_due_today_returns_10(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) + timedelta(hours=1))
        # days_until_due should be 0
        assert calc.calculate_urgency_score(task) == 10.0

    def test_due_tomorrow_returns_9(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) + timedelta(days=1, hours=1))
        assert calc.calculate_urgency_score(task) == 9.0

    def test_due_in_2_days(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) + timedelta(days=2, hours=1))
        assert calc.calculate_urgency_score(task) == 8.0

    def test_due_in_5_days(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) + timedelta(days=5, hours=1))
        assert calc.calculate_urgency_score(task) == 5.0

    def test_due_in_10_days(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) + timedelta(days=10, hours=1))
        # 10 - 10 = 0 → max(0, 0) = 0.0
        assert calc.calculate_urgency_score(task) == 0.0

    def test_due_in_15_days(self):
        calc = self._get_calculator()
        task = MockTask(due_date=datetime.now(timezone.utc) + timedelta(days=15))
        assert calc.calculate_urgency_score(task) == 0.0

    def test_no_due_date_returns_neutral(self):
        calc = self._get_calculator()
        task = MockTask(due_date=None)
        assert calc.calculate_urgency_score(task) == 5.0


# ===================================================================
# Weight impact scoring (no DB dependency)
# ===================================================================

class TestCalculateWeightImpactScore:

    def _get_calculator(self):
        from app.utils.priority_calculator import PriorityCalculator
        return PriorityCalculator

    def test_max_ca_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=30, category="CA")
        assert calc.calculate_weight_impact_score(task) == 10.0

    def test_half_ca_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=15, category="CA")
        assert calc.calculate_weight_impact_score(task) == 5.0

    def test_exam_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=65, category="EXAM")
        assert calc.calculate_weight_impact_score(task) == 10.0

    def test_half_exam_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=32.5, category="EXAM")
        assert calc.calculate_weight_impact_score(task) == 5.0

    def test_zero_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=0)
        assert calc.calculate_weight_impact_score(task) == 0.0

    def test_no_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=None)
        assert calc.calculate_weight_impact_score(task) == 0.0

    def test_small_ca_weight(self):
        calc = self._get_calculator()
        task = MockTask(weight=5, category="CA")
        expected = (5 / 30) * 10
        assert calc.calculate_weight_impact_score(task) == pytest.approx(expected, abs=0.01)

    def test_weight_capped_at_10(self):
        calc = self._get_calculator()
        # Even if weight exceeds max, score caps at 10
        task = MockTask(weight=40, category="CA")
        assert calc.calculate_weight_impact_score(task) == 10.0


# ===================================================================
# Mood score (requires DB mocking)
# ===================================================================

class TestCalculateMoodScore:

    def _get_calculator(self):
        from app.utils.priority_calculator import PriorityCalculator
        return PriorityCalculator

    def _setup_mock_db(self, mood_log=None):
        """Create a mock DB that returns the given mood log"""
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.first.return_value = mood_log
        return db

    def test_no_recent_mood_returns_neutral(self):
        calc = self._get_calculator()
        task = MockTask(weight=15)
        user = MockUser()
        db = self._setup_mock_db(mood_log=None)
        assert calc.calculate_mood_score(task, user, db) == 5.0

    def test_high_energy_prefers_heavy_tasks(self):
        calc = self._get_calculator()
        task = MockTask(weight=30)  # Heavy task
        user = MockUser()
        mood = MockMoodLog(mood_type="focused", energy_level=5)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 9.0

    def test_high_energy_medium_task(self):
        calc = self._get_calculator()
        task = MockTask(weight=25)  # Medium-heavy task
        user = MockUser()
        mood = MockMoodLog(mood_type="focused", energy_level=4)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 7.0

    def test_high_energy_light_task(self):
        calc = self._get_calculator()
        task = MockTask(weight=5)  # Light task
        user = MockUser()
        mood = MockMoodLog(mood_type="focused", energy_level=4)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 5.0

    def test_low_energy_prefers_light_tasks(self):
        calc = self._get_calculator()
        task = MockTask(weight=5)  # Light task
        user = MockUser()
        mood = MockMoodLog(mood_type="tired", energy_level=1)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 9.0

    def test_low_energy_medium_task(self):
        calc = self._get_calculator()
        task = MockTask(weight=15)  # Medium task
        user = MockUser()
        mood = MockMoodLog(mood_type="tired", energy_level=2)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 6.0

    def test_low_energy_heavy_task_bad_match(self):
        calc = self._get_calculator()
        task = MockTask(weight=30)  # Heavy task
        user = MockUser()
        mood = MockMoodLog(mood_type="tired", energy_level=1)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 3.0

    def test_stressed_prefers_quick_wins(self):
        calc = self._get_calculator()
        task = MockTask(weight=10)  # Quick win
        user = MockUser()
        mood = MockMoodLog(mood_type="stressed", energy_level=3)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 8.5

    def test_stressed_medium_task(self):
        calc = self._get_calculator()
        task = MockTask(weight=20)
        user = MockUser()
        mood = MockMoodLog(mood_type="anxious", energy_level=3)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 5.5

    def test_stressed_heavy_task_avoided(self):
        calc = self._get_calculator()
        task = MockTask(weight=30)
        user = MockUser()
        mood = MockMoodLog(mood_type="overwhelmed", energy_level=3)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 3.0

    def test_focused_prefers_heavy_tasks(self):
        calc = self._get_calculator()
        task = MockTask(weight=25)  # Heavy task
        user = MockUser()
        mood = MockMoodLog(mood_type="focused", energy_level=3)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 8.0

    def test_motivated_light_task_still_good(self):
        calc = self._get_calculator()
        task = MockTask(weight=10)
        user = MockUser()
        mood = MockMoodLog(mood_type="motivated", energy_level=3)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 7.0

    def test_medium_energy_neutral_mood(self):
        calc = self._get_calculator()
        task = MockTask(weight=15)
        user = MockUser()
        # Energy 3, mood "calm" → not stressed, not focused, medium energy → balanced
        mood = MockMoodLog(mood_type="calm", energy_level=3)
        db = self._setup_mock_db(mood_log=mood)
        assert calc.calculate_mood_score(task, user, db) == 6.0


# ===================================================================
# Goal impact score (requires DB mocking)
# ===================================================================

class TestCalculateGoalImpactScore:

    def _get_calculator(self):
        from app.utils.priority_calculator import PriorityCalculator
        return PriorityCalculator

    def test_no_target_cgpa_returns_neutral(self):
        calc = self._get_calculator()
        task = MockTask(weight=15)
        user = MockUser(target_cgpa=None)
        db = MagicMock()
        assert calc.calculate_goal_impact_score(task, user, db) == 5.0

    @patch('app.utils.cgpa_calculator.CGPACalculator.get_user_cgpa_data')
    def test_already_exceeding_target(self, mock_get_data):
        calc = self._get_calculator()
        task = MockTask(weight=15)
        user = MockUser(target_cgpa=3.5, current_cgpa=4.0)

        mock_get_data.return_value = {
            'current': {'cgpa': 4.0}
        }
        db = MagicMock()
        result = calc.calculate_goal_impact_score(task, user, db)
        assert result == 5.0

    @patch('app.utils.cgpa_calculator.CGPACalculator.get_user_cgpa_data')
    def test_large_gap_high_impact(self, mock_get_data):
        calc = self._get_calculator()
        task = MockTask(weight=30)
        user = MockUser(target_cgpa=4.5, current_cgpa=2.5)

        mock_get_data.return_value = {
            'current': {'cgpa': 2.5}
        }
        db = MagicMock()
        result = calc.calculate_goal_impact_score(task, user, db)
        # gap = 2.0, gap_score = 10.0, weight_multiplier = 30/100 = 0.3
        # result = min(10, 10 * 1.3) = 10.0 (capped)
        assert result == 10.0

    @patch('app.utils.cgpa_calculator.CGPACalculator.get_user_cgpa_data')
    def test_small_gap_moderate_impact(self, mock_get_data):
        calc = self._get_calculator()
        task = MockTask(weight=15)
        user = MockUser(target_cgpa=4.5, current_cgpa=4.0)

        mock_get_data.return_value = {
            'current': {'cgpa': 4.0}
        }
        db = MagicMock()
        result = calc.calculate_goal_impact_score(task, user, db)
        # gap = 0.5, gap_score = (0.5/2.0)*10 = 2.5, weight_mult = 15/100 = 0.15
        # result = 2.5 * 1.15 = 2.875
        assert result == pytest.approx(2.875, abs=0.01)

    @patch('app.utils.cgpa_calculator.CGPACalculator.get_user_cgpa_data')
    def test_error_returns_neutral(self, mock_get_data):
        calc = self._get_calculator()
        task = MockTask(weight=15)
        user = MockUser(target_cgpa=4.5)

        mock_get_data.side_effect = Exception("DB error")
        db = MagicMock()
        result = calc.calculate_goal_impact_score(task, user, db)
        assert result == 5.0


# ===================================================================
# Full priority score calculation (requires DB mocking)
# ===================================================================

class TestCalculatePriorityScore:

    def _get_calculator(self):
        from app.utils.priority_calculator import PriorityCalculator
        return PriorityCalculator

    @patch.object(
        __import__('app.utils.priority_calculator', fromlist=['PriorityCalculator']).PriorityCalculator,
        'calculate_mood_score', return_value=5.0
    )
    @patch.object(
        __import__('app.utils.priority_calculator', fromlist=['PriorityCalculator']).PriorityCalculator,
        'calculate_goal_impact_score', return_value=5.0
    )
    def test_priority_score_formula(self, mock_goal, mock_mood):
        calc = self._get_calculator()
        task = MockTask(
            due_date=datetime.now(timezone.utc) + timedelta(hours=1),  # urgency = 10
            weight=30,  # weight = 10
            category="CA"
        )
        user = MockUser()
        db = MagicMock()

        result = calc.calculate_priority_score(task, user, db)

        assert 'priority_score' in result
        assert 'urgency_score' in result
        assert 'weight_score' in result
        assert 'mood_score' in result
        assert 'goal_score' in result

        # 0.4*10 + 0.3*10 + 0.15*5 + 0.15*5 = 4 + 3 + 0.75 + 0.75 = 8.5
        assert result['priority_score'] == pytest.approx(8.5, abs=0.01)
        assert result['urgency_score'] == 10.0
        assert result['weight_score'] == 10.0

    @patch.object(
        __import__('app.utils.priority_calculator', fromlist=['PriorityCalculator']).PriorityCalculator,
        'calculate_mood_score', return_value=0.0
    )
    @patch.object(
        __import__('app.utils.priority_calculator', fromlist=['PriorityCalculator']).PriorityCalculator,
        'calculate_goal_impact_score', return_value=0.0
    )
    def test_minimum_priority_score(self, mock_goal, mock_mood):
        calc = self._get_calculator()
        task = MockTask(
            due_date=datetime.now(timezone.utc) + timedelta(days=15),  # urgency = 0
            weight=0,  # weight = 0
        )
        user = MockUser()
        db = MagicMock()

        result = calc.calculate_priority_score(task, user, db)
        assert result['priority_score'] == 0.0


# ===================================================================
# Recommendation type classification
# ===================================================================

class TestGetRecommendationType:

    def _get_calculator(self):
        from app.utils.priority_calculator import PriorityCalculator
        return PriorityCalculator

    def test_urgent_type(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 9.0,
            "goal_score": 3.0,
            "mood_score": 5.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "urgent"

    def test_urgent_at_boundary(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 8.0,
            "goal_score": 3.0,
            "mood_score": 5.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "urgent"

    def test_goal_driven_type(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 3.0,
            "goal_score": 8.0,
            "mood_score": 5.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "goal_driven"

    def test_goal_driven_at_boundary(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 3.0,
            "goal_score": 7.0,
            "mood_score": 5.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "goal_driven"

    def test_mood_based_type(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 3.0,
            "goal_score": 3.0,
            "mood_score": 9.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "mood_based"

    def test_mood_based_at_boundary(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 3.0,
            "goal_score": 3.0,
            "mood_score": 8.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "mood_based"

    def test_recovery_type(self):
        calc = self._get_calculator()
        task = MockTask()
        # goal must be < 7 to avoid goal_driven match, but >= 6 for recovery
        breakdown = {
            "urgency_score": 7.0,
            "goal_score": 6.5,
            "mood_score": 3.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "recovery"

    def test_recovery_at_boundary(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 6.0,
            "goal_score": 6.0,
            "mood_score": 3.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "recovery"

    def test_default_is_goal_driven(self):
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 3.0,
            "goal_score": 3.0,
            "mood_score": 3.0,
            "weight_score": 3.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "goal_driven"

    def test_urgent_takes_priority_over_goal(self):
        """If urgency >= 8, it should be 'urgent' even if goal >= 7"""
        calc = self._get_calculator()
        task = MockTask()
        breakdown = {
            "urgency_score": 9.0,
            "goal_score": 9.0,
            "mood_score": 9.0,
            "weight_score": 5.0,
        }
        assert calc.get_recommendation_type(task, breakdown) == "urgent"


# ===================================================================
# Priority weight constants
# ===================================================================

class TestPriorityWeights:

    def test_weights_sum_to_one(self):
        from app.utils.priority_calculator import PriorityCalculator as calc
        total = (
            calc.URGENCY_WEIGHT
            + calc.WEIGHT_IMPACT_WEIGHT
            + calc.MOOD_WEIGHT
            + calc.GOAL_IMPACT_WEIGHT
        )
        assert total == pytest.approx(1.0)

    def test_urgency_is_dominant_factor(self):
        from app.utils.priority_calculator import PriorityCalculator as calc
        assert calc.URGENCY_WEIGHT > calc.WEIGHT_IMPACT_WEIGHT
        assert calc.URGENCY_WEIGHT > calc.MOOD_WEIGHT
        assert calc.URGENCY_WEIGHT > calc.GOAL_IMPACT_WEIGHT

    def test_weight_impact_is_second(self):
        from app.utils.priority_calculator import PriorityCalculator as calc
        assert calc.WEIGHT_IMPACT_WEIGHT > calc.MOOD_WEIGHT
        assert calc.WEIGHT_IMPACT_WEIGHT > calc.GOAL_IMPACT_WEIGHT

    def test_mood_and_goal_equal(self):
        from app.utils.priority_calculator import PriorityCalculator as calc
        assert calc.MOOD_WEIGHT == calc.GOAL_IMPACT_WEIGHT
