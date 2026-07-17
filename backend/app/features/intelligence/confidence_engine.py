"""Confidence Engine for AI suggestion scoring and thresholding.

AI suggestions include confidence scores. The confidence engine:
- Calculates confidence levels (HIGH, MEDIUM, LOW)
- Determines if suggestions should be auto-applied
- Requires user confirmation for low-confidence suggestions
- Tracks confidence metrics over time
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.features.intelligence.models import (
    AICategory,
    AIMerchant,
    ConfidenceLevel,
)

MIN_VIABLE_CONFIDENCE = 0.40



@dataclass(frozen=True)
class ConfidenceThresholds:
    """Configurable confidence thresholds."""
    high_threshold: float = 0.85  # >= 0.85 = HIGH
    medium_threshold: float = 0.70  # >= 0.70 = MEDIUM, else LOW
    auto_apply_threshold: float = 0.90  # Minimum confidence to auto-apply


class ConfidenceEngine:
    """Calculates and manages confidence scores for AI suggestions."""

    def __init__(self, thresholds: ConfidenceThresholds | None = None):
        """Initialize confidence engine.
        
        Args:
            thresholds: Custom confidence thresholds
        """
        self.thresholds = thresholds or ConfidenceThresholds()

    def calculate_confidence_level(self, score: float) -> ConfidenceLevel:
        """Map confidence score (0.0-1.0) to confidence level.
        
        Args:
            score: Confidence score between 0.0 and 1.0
            
        Returns:
            ConfidenceLevel (HIGH, MEDIUM, or LOW)
        """
        if score >= self.thresholds.high_threshold:
            return ConfidenceLevel.HIGH
        elif score >= self.thresholds.medium_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def should_auto_apply(
        self,
        score: float,
        level: ConfidenceLevel | None = None,
    ) -> bool:
        """Determine if suggestion should be automatically applied.
        
        Args:
            score: Confidence score
            level: Pre-calculated confidence level (optional)
            
        Returns:
            True if score exceeds auto-apply threshold
        """
        return score >= self.thresholds.auto_apply_threshold

    def should_require_confirmation(
        self,
        score: float,
        level: ConfidenceLevel | None = None,
    ) -> bool:
        """Determine if user confirmation is required.
        
        Args:
            score: Confidence score
            level: Pre-calculated confidence level (optional)
            
        Returns:
            True if confirmation is needed (anything below HIGH)
        """
        if level is None:
            level = self.calculate_confidence_level(score)

        return level != ConfidenceLevel.HIGH

    def should_reject(
        self,
        score: float,
        level: ConfidenceLevel | None = None,
    ) -> bool:
        """Determine if suggestion should be rejected outright.
        
        Very low confidence suggestions might not be shown at all.
        
        Args:
            score: Confidence score
            level: Pre-calculated confidence level (optional)
            
        Returns:
            True if suggestion should be hidden
        """
        if level is None:
            level = self.calculate_confidence_level(score)

        return score < MIN_VIABLE_CONFIDENCE  # Arbitrary low threshold

    def adjust_category_suggestion(
        self,
        suggestion: AICategory,
    ) -> AICategory:
        """Adjust category suggestion with proper confidence level.
        
        Args:
            suggestion: Original suggestion from AI
            
        Returns:
            Adjusted suggestion with proper confidence level
        """
        level = self.calculate_confidence_level(suggestion.confidence)
        return AICategory(
            category=suggestion.category,
            confidence=suggestion.confidence,
            confidence_level=level,
            reasoning=suggestion.reasoning,
        )

    def adjust_merchant_suggestion(
        self,
        suggestion: AIMerchant,
    ) -> AIMerchant:
        """Adjust merchant suggestion with proper confidence level.
        
        Args:
            suggestion: Original suggestion from AI
            
        Returns:
            Adjusted suggestion with proper confidence level
        """
        level = self.calculate_confidence_level(suggestion.confidence)
        return AIMerchant(
            merchant=suggestion.merchant,
            confidence=suggestion.confidence,
            confidence_level=level,
            reasoning=suggestion.reasoning,
        )

    def evaluate_confidence_breakdown(
        self,
        score: float,
    ) -> dict[str, Any]:
        """Provide detailed breakdown of confidence score.
        
        Args:
            score: Confidence score (0.0-1.0)
            
        Returns:
            Dictionary with confidence analysis
        """
        level = self.calculate_confidence_level(score)
        percentage = int(score * 100)

        return {
            "score": score,
            "percentage": percentage,
            "level": level.value,
            "auto_apply": self.should_auto_apply(score, level),
            "requires_confirmation": self.should_require_confirmation(score, level),
            "should_show": not self.should_reject(score, level),
            "thresholds": {
                "low": 0,
                "medium": int(self.thresholds.medium_threshold * 100),
                "high": int(self.thresholds.high_threshold * 100),
                "auto_apply": int(self.thresholds.auto_apply_threshold * 100),
            },
        }


class ConfidenceScoreCalculator:
    """Calculates confidence scores for various AI tasks.
    
    These are reference implementations - actual scoring depends on
    the AI provider's confidence values.
    """

    @staticmethod
    def calculate_category_confidence(
        ai_score: float,
        rule_match: bool = False,
        memory_match: bool = False,
    ) -> float:
        """Calculate final category confidence.
        
        Args:
            ai_score: Base confidence from AI model
            rule_match: Whether a rule also suggests this category
            memory_match: Whether merchant memory also suggests this category
            
        Returns:
            Adjusted confidence score (0.0-1.0)
        """
        score = ai_score

        # Boost confidence if other signals agree
        if rule_match:
            score = min(1.0, score + 0.10)
        if memory_match:
            score = min(1.0, score + 0.05)

        return score

    @staticmethod
    def calculate_merchant_confidence(
        ai_score: float,
        similarity_to_previous: float | None = None,
    ) -> float:
        """Calculate final merchant confidence.
        
        Args:
            ai_score: Base confidence from AI model
            similarity_to_previous: Similarity to previously seen merchants
            
        Returns:
            Adjusted confidence score (0.0-1.0)
        """
        score = ai_score

        # Boost if similar to known merchants
        if similarity_to_previous is not None and similarity_to_previous > 0.7:
            score = min(1.0, score + 0.15)

        return score

    @staticmethod
    def calculate_insight_confidence(
        base_score: float,
        data_points: int,
        trend_consistency: float = 0.5,
    ) -> float:
        """Calculate confidence in an automatically-generated insight.
        
        Args:
            base_score: Base confidence score
            data_points: Number of data points supporting insight
            trend_consistency: How consistent the trend is (0.0-1.0)
            
        Returns:
            Adjusted confidence score (0.0-1.0)
        """
        score = base_score

        # More data points increase confidence (up to a limit)
        data_factor = min(1.0, data_points / 30.0)
        score = score * 0.7 + (trend_consistency * 0.3)
        score = score * (0.8 + (data_factor * 0.2))

        return max(0.0, min(1.0, score))
