"""Unit tests for the ConfidenceEngine."""

import unittest

from backend.app.features.intelligence.confidence_engine import (
    ConfidenceEngine,
    ConfidenceThresholds,
    MIN_VIABLE_CONFIDENCE,
)
from backend.app.features.intelligence.models import ConfidenceLevel


class TestConfidenceThresholds(unittest.TestCase):
    def test_defaults(self) -> None:
        t = ConfidenceThresholds()
        self.assertEqual(t.high_threshold, 0.85)
        self.assertEqual(t.medium_threshold, 0.70)
        self.assertEqual(t.auto_apply_threshold, 0.90)


class TestConfidenceEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ConfidenceEngine()

    def test_high_confidence_level(self) -> None:
        self.assertEqual(self.engine.calculate_confidence_level(1.0), ConfidenceLevel.HIGH)
        self.assertEqual(self.engine.calculate_confidence_level(0.85), ConfidenceLevel.HIGH)
        self.assertEqual(self.engine.calculate_confidence_level(0.95), ConfidenceLevel.HIGH)

    def test_medium_confidence_level(self) -> None:
        self.assertEqual(self.engine.calculate_confidence_level(0.84), ConfidenceLevel.MEDIUM)
        self.assertEqual(self.engine.calculate_confidence_level(0.70), ConfidenceLevel.MEDIUM)

    def test_low_confidence_level(self) -> None:
        self.assertEqual(self.engine.calculate_confidence_level(0.69), ConfidenceLevel.LOW)
        self.assertEqual(self.engine.calculate_confidence_level(0.0), ConfidenceLevel.LOW)

    def test_should_auto_apply_above_threshold(self) -> None:
        self.assertTrue(self.engine.should_auto_apply(0.90))
        self.assertTrue(self.engine.should_auto_apply(1.0))

    def test_should_not_auto_apply_below_threshold(self) -> None:
        self.assertFalse(self.engine.should_auto_apply(0.89))
        self.assertFalse(self.engine.should_auto_apply(0.50))

    def test_should_require_confirmation_below_high(self) -> None:
        self.assertTrue(self.engine.should_require_confirmation(0.50))
        self.assertTrue(self.engine.should_require_confirmation(0.70))

    def test_should_not_require_confirmation_at_high(self) -> None:
        self.assertFalse(self.engine.should_require_confirmation(0.90))
        self.assertFalse(self.engine.should_require_confirmation(1.0))

    def test_should_reject_below_min_viable(self) -> None:
        self.assertTrue(self.engine.should_reject(0.0))
        self.assertTrue(self.engine.should_reject(0.39))
        self.assertTrue(self.engine.should_reject(MIN_VIABLE_CONFIDENCE - 0.01))

    def test_should_not_reject_at_or_above_min_viable(self) -> None:
        self.assertFalse(self.engine.should_reject(MIN_VIABLE_CONFIDENCE))
        self.assertFalse(self.engine.should_reject(0.80))
        self.assertFalse(self.engine.should_reject(1.0))

    def test_min_viable_confidence_value(self) -> None:
        self.assertEqual(MIN_VIABLE_CONFIDENCE, 0.40)

    def test_custom_thresholds(self) -> None:
        custom = ConfidenceThresholds(high_threshold=0.95, medium_threshold=0.80, auto_apply_threshold=0.98)
        engine = ConfidenceEngine(thresholds=custom)
        self.assertEqual(engine.calculate_confidence_level(0.96), ConfidenceLevel.HIGH)
        self.assertEqual(engine.calculate_confidence_level(0.82), ConfidenceLevel.MEDIUM)
        self.assertEqual(engine.calculate_confidence_level(0.79), ConfidenceLevel.LOW)
        self.assertTrue(engine.should_auto_apply(0.98))
        self.assertFalse(engine.should_auto_apply(0.97))


if __name__ == "__main__":
    unittest.main()
