"""Anomaly Calibration & Evaluation Engine (DO-12).

Provides backtesting metrics (precision, recall, F1, FPR, FNR) and method ablation
testing to validate detection performance against labelled ground truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AnomalyEvaluationMetrics:
    """Standard evaluation metrics for anomaly detectors."""
    total_cases: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cases": self.total_cases,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
        }


class AnomalyCalibrator:
    """Evaluates and calibrates anomaly detection accuracy and error rates."""

    @classmethod
    def evaluate_predictions(
        cls,
        predictions: List[bool],
        ground_truth: List[bool],
    ) -> AnomalyEvaluationMetrics:
        """Calculate confusion matrix, precision, recall, and F1 score."""
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth arrays must have identical length.")

        tp = sum(1 for p, g in zip(predictions, ground_truth) if p and g)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p and not g)
        tn = sum(1 for p, g in zip(predictions, ground_truth) if not p and not g)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if not p and g)

        total = len(predictions)
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        fpr = (fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = (fn / (fn + tp)) if (fn + tp) > 0 else 0.0

        return AnomalyEvaluationMetrics(
            total_cases=total,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            f1_score=f1,
            false_positive_rate=fpr,
            false_negative_rate=fnr,
        )
