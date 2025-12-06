"""Tests for SM-2 spaced repetition algorithm (logic layer)."""
from __future__ import annotations

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from domain.sr.logic import (
    SM2Result,
    QUALITY_MAP,
    map_response_to_quality,
    compute_sm2,
)


class TestQualityMapping:
    """Tests for response to quality mapping."""

    def test_got_it_maps_to_5(self):
        """Test 'got_it' response maps to quality 5."""
        assert map_response_to_quality("got_it") == 5

    def test_meh_maps_to_3(self):
        """Test 'meh' response maps to quality 3."""
        assert map_response_to_quality("meh") == 3

    def test_forgot_maps_to_1(self):
        """Test 'forgot' response maps to quality 1."""
        assert map_response_to_quality("forgot") == 1

    def test_case_insensitive_mapping(self):
        """Test that mapping is case-insensitive."""
        assert map_response_to_quality("GOT_IT") == 5
        assert map_response_to_quality("Got_It") == 5
        assert map_response_to_quality("MEH") == 3
        assert map_response_to_quality("FORGOT") == 1

    def test_unknown_response_raises_error(self):
        """Test that unknown response raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            map_response_to_quality("unknown")
        assert "Unknown response" in str(exc_info.value)

    def test_empty_response_raises_error(self):
        """Test that empty response raises ValueError."""
        with pytest.raises(ValueError):
            map_response_to_quality("")

    def test_quality_map_constant_values(self):
        """Test QUALITY_MAP has correct values."""
        assert QUALITY_MAP == {"got_it": 5, "meh": 3, "forgot": 1}


class TestSM2AlgorithmBasics:
    """Basic tests for SM-2 algorithm computation."""

    def test_first_review_got_it(self):
        """Test first review with 'got_it' response."""
        result = compute_sm2(
            prev_repetition=0,
            prev_interval=0,
            prev_ef=2.5,
            response="got_it",
        )
        
        assert result.repetition == 1
        assert result.interval_days == 1
        assert result.quality == 5
        # EF should increase slightly for quality 5
        assert result.ef >= 2.5

    def test_second_review_got_it(self):
        """Test second review with 'got_it' response."""
        result = compute_sm2(
            prev_repetition=1,
            prev_interval=1,
            prev_ef=2.5,
            response="got_it",
        )
        
        assert result.repetition == 2
        assert result.interval_days == 6  # SM-2 standard for rep 2
        assert result.quality == 5

    def test_third_review_got_it(self):
        """Test third review with 'got_it' response."""
        result = compute_sm2(
            prev_repetition=2,
            prev_interval=6,
            prev_ef=2.5,
            response="got_it",
        )
        
        assert result.repetition == 3
        # interval = round(6 * 2.6) = 16 (EF increases for quality 5)
        assert result.interval_days >= 15
        assert result.quality == 5

    def test_forgot_resets_repetition(self):
        """Test that 'forgot' resets repetition to 0."""
        result = compute_sm2(
            prev_repetition=5,
            prev_interval=30,
            prev_ef=2.5,
            response="forgot",
        )
        
        assert result.repetition == 0
        assert result.interval_days == 1
        assert result.quality == 1

    def test_meh_increments_repetition(self):
        """Test that 'meh' (quality 3) still increments repetition."""
        result = compute_sm2(
            prev_repetition=1,
            prev_interval=1,
            prev_ef=2.5,
            response="meh",
        )
        
        assert result.repetition == 2
        assert result.interval_days == 6
        assert result.quality == 3


class TestSM2EasinessFactor:
    """Tests for easiness factor (EF) calculations."""

    def test_ef_increases_for_quality_5(self):
        """Test EF increases when quality is 5."""
        result = compute_sm2(
            prev_repetition=2,
            prev_interval=6,
            prev_ef=2.5,
            response="got_it",
        )
        
        # EF formula: 2.5 + (0.1 - (5-5)*(0.08 + (5-5)*0.02)) = 2.5 + 0.1 = 2.6
        assert result.ef == 2.6

    def test_ef_decreases_for_quality_3(self):
        """Test EF decreases when quality is 3."""
        result = compute_sm2(
            prev_repetition=2,
            prev_interval=6,
            prev_ef=2.5,
            response="meh",
        )
        
        # EF formula: 2.5 + (0.1 - (5-3)*(0.08 + (5-3)*0.02)) = 2.5 + 0.1 - 0.24 = 2.36
        assert result.ef == 2.36

    def test_ef_decreases_for_quality_1(self):
        """Test EF decreases significantly when quality is 1."""
        result = compute_sm2(
            prev_repetition=2,
            prev_interval=6,
            prev_ef=2.5,
            response="forgot",
        )
        
        # EF formula: 2.5 + (0.1 - (5-1)*(0.08 + (5-1)*0.02)) = 2.5 + 0.1 - 0.64 = 1.96
        assert result.ef == 1.96

    def test_ef_minimum_is_1_3(self):
        """Test EF cannot go below 1.3."""
        result = compute_sm2(
            prev_repetition=2,
            prev_interval=6,
            prev_ef=1.3,  # Already at minimum
            response="forgot",
        )
        
        assert result.ef == 1.3

    def test_ef_maximum_is_5_0(self):
        """Test EF cannot exceed 5.0."""
        result = compute_sm2(
            prev_repetition=10,
            prev_interval=100,
            prev_ef=4.95,
            response="got_it",
        )
        
        assert result.ef <= 5.0

    def test_ef_stays_at_minimum_after_multiple_failures(self):
        """Test EF stays at 1.3 even after multiple failures."""
        ef = 2.5
        for _ in range(10):
            result = compute_sm2(
                prev_repetition=1,
                prev_interval=1,
                prev_ef=ef,
                response="forgot",
            )
            ef = result.ef
        
        assert ef == 1.3


class TestSM2IntervalCalculation:
    """Tests for interval calculation."""

    def test_interval_minimum_is_1_day(self):
        """Test interval never goes below 1 day."""
        result = compute_sm2(
            prev_repetition=0,
            prev_interval=0,
            prev_ef=1.3,
            response="got_it",
        )
        
        assert result.interval_days >= 1

    def test_interval_grows_with_ef(self):
        """Test interval grows proportionally with EF."""
        result_low_ef = compute_sm2(
            prev_repetition=3,
            prev_interval=15,
            prev_ef=1.5,
            response="got_it",
        )
        
        result_high_ef = compute_sm2(
            prev_repetition=3,
            prev_interval=15,
            prev_ef=3.0,
            response="got_it",
        )
        
        assert result_high_ef.interval_days > result_low_ef.interval_days

    def test_interval_is_rounded(self):
        """Test that interval is rounded to nearest integer."""
        result = compute_sm2(
            prev_repetition=3,
            prev_interval=7,
            prev_ef=2.5,
            response="got_it",
        )
        
        assert isinstance(result.interval_days, int)

    def test_long_term_interval_growth(self):
        """Test interval grows appropriately over many reviews."""
        rep = 0
        interval = 0
        ef = 2.5
        
        for _ in range(10):
            result = compute_sm2(
                prev_repetition=rep,
                prev_interval=interval,
                prev_ef=ef,
                response="got_it",
            )
            rep = result.repetition
            interval = result.interval_days
            ef = result.ef
        
        # After 10 successful reviews, interval should be substantial
        assert interval > 100


class TestSM2EdgeCases:
    """Edge case tests for SM-2 algorithm."""

    def test_fresh_card_state(self):
        """Test computation with fresh card (all zeros)."""
        result = compute_sm2(
            prev_repetition=0,
            prev_interval=0,
            prev_ef=2.5,
            response="got_it",
        )
        
        assert result.repetition == 1
        assert result.interval_days == 1
        assert result.ef >= 2.5

    def test_very_high_repetition_count(self):
        """Test with very high repetition count."""
        result = compute_sm2(
            prev_repetition=100,
            prev_interval=365,
            prev_ef=2.8,
            response="got_it",
        )
        
        assert result.repetition == 101
        assert result.interval_days > 365

    def test_failure_after_long_streak(self):
        """Test failing after a long streak of successes."""
        result = compute_sm2(
            prev_repetition=20,
            prev_interval=180,
            prev_ef=2.8,
            response="forgot",
        )
        
        # Should reset completely
        assert result.repetition == 0
        assert result.interval_days == 1

    def test_recovery_after_failure(self):
        """Test recovery path after a failure."""
        # First, fail
        result1 = compute_sm2(
            prev_repetition=5,
            prev_interval=30,
            prev_ef=2.5,
            response="forgot",
        )
        
        # Then succeed
        result2 = compute_sm2(
            prev_repetition=result1.repetition,
            prev_interval=result1.interval_days,
            prev_ef=result1.ef,
            response="got_it",
        )
        
        assert result2.repetition == 1
        assert result2.interval_days == 1

    def test_consistent_meh_responses(self):
        """Test progression with consistent 'meh' responses."""
        rep = 0
        interval = 0
        ef = 2.5
        
        for _ in range(5):
            result = compute_sm2(
                prev_repetition=rep,
                prev_interval=interval,
                prev_ef=ef,
                response="meh",
            )
            rep = result.repetition
            interval = result.interval_days
            ef = result.ef
        
        # EF should have decreased, but repetition should increase
        assert rep == 5
        assert ef < 2.5
        assert ef >= 1.3


class TestSM2ResultDataclass:
    """Tests for SM2Result dataclass."""

    def test_result_has_all_fields(self):
        """Test SM2Result contains all required fields."""
        result = compute_sm2(0, 0, 2.5, "got_it")
        
        assert hasattr(result, "repetition")
        assert hasattr(result, "interval_days")
        assert hasattr(result, "ef")
        assert hasattr(result, "quality")

    def test_result_types(self):
        """Test SM2Result field types."""
        result = compute_sm2(0, 0, 2.5, "got_it")
        
        assert isinstance(result.repetition, int)
        assert isinstance(result.interval_days, int)
        assert isinstance(result.ef, float)
        assert isinstance(result.quality, int)

    def test_result_is_immutable_dataclass(self):
        """Test that SM2Result is a proper dataclass."""
        result = SM2Result(repetition=1, interval_days=1, ef=2.5, quality=5)
        
        assert result.repetition == 1
        assert result.interval_days == 1
        assert result.ef == 2.5
        assert result.quality == 5

