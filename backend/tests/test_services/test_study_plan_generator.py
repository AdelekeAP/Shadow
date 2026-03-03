"""
Tests for Study Plan Generator Service
backend/app/services/study_plan_generator.py

Tests the pure function calculate_optimal_duration and the JSON parser.
"""
import pytest

from app.services.study_plan_generator import (
    calculate_optimal_duration,
    parse_study_plan_json,
)


# ===================================================================
# calculate_optimal_duration
# ===================================================================

class TestCalculateOptimalDuration:

    def test_base_duration_empty_context(self):
        """Empty context: base 7, no moods, tasks=[] -> incomplete=0 < 3 -> +2 = 9"""
        result = calculate_optimal_duration({}, "BST")
        assert result == 9

    def test_high_cgpa_gap_shortens_plan(self):
        """cgpa_gap > 0.5 -> -2 = 5, then tasks < 3 -> +2 = 7"""
        context = {"cgpa_gap": 1.0}
        result = calculate_optimal_duration(context, "BST")
        assert result == 7

    def test_low_cgpa_gap_lengthens_plan(self):
        """cgpa_gap < 0.2 -> +3 = 10, then tasks < 3 -> +2 = 12"""
        context = {"cgpa_gap": 0.1}
        result = calculate_optimal_duration(context, "BST")
        assert result == 12

    def test_low_energy_lengthens_plan(self):
        """energy_level <= 2 -> +2 = 9, then tasks < 3 -> +2 = 11"""
        context = {"recent_moods": [{"energy_level": 1}]}
        result = calculate_optimal_duration(context, "BST")
        assert result == 11

    def test_high_energy_shortens_plan(self):
        """energy_level >= 4 -> -1 = 6, then tasks < 3 -> +2 = 8"""
        context = {"recent_moods": [{"energy_level": 5}]}
        result = calculate_optimal_duration(context, "BST")
        assert result == 8

    def test_many_incomplete_tasks_shortens_plan(self):
        """incomplete > 10 -> -2 = 5"""
        tasks = [{"is_completed": False} for _ in range(12)]
        context = {"recent_tasks": tasks}
        result = calculate_optimal_duration(context, "BST")
        assert result == 5

    def test_few_incomplete_tasks_lengthens_plan(self):
        """incomplete=1 < 3 -> +2 = 9"""
        tasks = [{"is_completed": True}, {"is_completed": False}]
        context = {"recent_tasks": tasks}
        result = calculate_optimal_duration(context, "BST")
        assert result == 9

    def test_never_below_5(self):
        """Maximum shortening combo should still not go below 5"""
        tasks = [{"is_completed": False} for _ in range(15)]
        context = {
            "cgpa_gap": 1.5,
            "recent_moods": [{"energy_level": 5}],
            "recent_tasks": tasks,
        }
        result = calculate_optimal_duration(context, "BST")
        assert result >= 5

    def test_never_above_14(self):
        """Maximum lengthening combo should still not exceed 14"""
        context = {
            "cgpa_gap": 0.05,
            "recent_moods": [{"energy_level": 1}],
            "recent_tasks": [],
        }
        result = calculate_optimal_duration(context, "BST")
        assert result <= 14

    def test_moderate_context_in_range(self):
        """A moderate context stays within the valid range"""
        context = {
            "cgpa_gap": 0.3,
            "recent_moods": [{"energy_level": 3}],
            "recent_tasks": [{"is_completed": False} for _ in range(5)],
        }
        result = calculate_optimal_duration(context, "BST")
        assert 5 <= result <= 14

    def test_topic_does_not_affect_duration(self):
        """The topic parameter does not change the result"""
        ctx = {"cgpa_gap": 0.5}
        assert calculate_optimal_duration(ctx, "BST") == calculate_optimal_duration(ctx, "Sorting")

    def test_cgpa_gap_zero_no_adjustment(self):
        """cgpa_gap=0 is falsy -> no gap adjustment, tasks < 3 -> +2 = 9"""
        context = {"cgpa_gap": 0}
        result = calculate_optimal_duration(context, "BST")
        assert result == 9

    def test_energy_level_3_no_mood_adjustment(self):
        """energy_level=3 -> no mood adjustment (not <=2 and not >=4), tasks < 3 -> +2 = 9"""
        context = {"recent_moods": [{"energy_level": 3}]}
        result = calculate_optimal_duration(context, "BST")
        assert result == 9

    def test_exactly_10_incomplete_tasks_no_adjustment(self):
        """incomplete == 10 -> not > 10 and not < 3 -> no task adjustment"""
        tasks = [{"is_completed": False} for _ in range(10)]
        context = {"recent_tasks": tasks}
        result = calculate_optimal_duration(context, "BST")
        assert result == 7

    def test_all_tasks_completed_counts_as_few(self):
        """All completed -> incomplete=0 < 3 -> +2"""
        tasks = [{"is_completed": True} for _ in range(20)]
        context = {"recent_tasks": tasks}
        result = calculate_optimal_duration(context, "BST")
        assert result == 9


# ===================================================================
# parse_study_plan_json
# ===================================================================

class TestParseStudyPlanJson:

    def test_valid_json(self):
        raw = '{"title": "Plan", "description": "Desc", "days": [{"day_number": 1, "activities": []}]}'
        result = parse_study_plan_json(raw)
        assert result["title"] == "Plan"
        assert len(result["days"]) == 1

    def test_strips_markdown_code_blocks(self):
        raw = '```json\n{"title": "Plan", "description": "Desc", "days": [{"day_number": 1, "activities": []}]}\n```'
        result = parse_study_plan_json(raw)
        assert result["title"] == "Plan"

    def test_missing_required_field_raises(self):
        raw = '{"title": "Plan", "days": [{"day_number": 1, "activities": []}]}'
        with pytest.raises(ValueError, match="Missing required field"):
            parse_study_plan_json(raw)

    def test_empty_days_raises(self):
        raw = '{"title": "Plan", "description": "Desc", "days": []}'
        with pytest.raises(ValueError, match="empty or invalid"):
            parse_study_plan_json(raw)

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_study_plan_json("not json at all")

    def test_day_missing_activities_raises(self):
        raw = '{"title": "Plan", "description": "Desc", "days": [{"day_number": 1}]}'
        with pytest.raises(ValueError, match="missing required fields"):
            parse_study_plan_json(raw)
