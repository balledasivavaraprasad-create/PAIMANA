"""Historical Snapshot Temporal Validation Engine (TI-01).

Validates chronological sequence, checks for duplicate snapshots, measures missing
periods, and computes historical coverage ratios.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .schemas import HistoricalCoverageReport


class TemporalValidator:
    """Validates chronological continuity and data quality of snapshot sequences."""

    @classmethod
    def validate_snapshots(
        cls,
        snapshots: List[Dict[str, Any]],
        expected_interval_months: int = 1,
    ) -> Tuple[List[Dict[str, Any]], HistoricalCoverageReport]:
        """Validate, sort chronologically, and assess coverage of project snapshots.

        Returns (sorted_clean_snapshots, coverage_report).
        """
        if not snapshots:
            rep = HistoricalCoverageReport(
                available_snapshots=0,
                expected_snapshots=0,
                coverage_ratio=0.0,
                missing_periods=0,
                temporal_quality="INSUFFICIENT",
                is_chronological=False,
                has_duplicates=False,
                date_range=(None, None),
            )
            return [], rep

        # Extract sequence keys
        keyed_snapshots = []
        has_duplicates = False
        seen_dates = set()

        for idx, s in enumerate(snapshots):
            # Resolve chronological key
            date_str = (
                s.get("report_month")
                or s.get("report_date")
                or s.get("as_of_date")
                or s.get("date")
            )
            sort_val = None

            if date_str:
                date_clean = str(date_str).strip()
                if date_clean in seen_dates:
                    has_duplicates = True
                seen_dates.add(date_clean)
                sort_val = cls._parse_date_to_index(date_clean)

            if sort_val is None:
                sort_val = s.get("report_index", idx)

            keyed_snapshots.append((sort_val, date_str, s))

        # Check if already chronological
        is_chronological = all(
            keyed_snapshots[i][0] <= keyed_snapshots[i + 1][0]
            for i in range(len(keyed_snapshots) - 1)
        )

        # Sort chronologically
        keyed_snapshots.sort(key=lambda x: x[0])
        sorted_clean = [item[2] for item in keyed_snapshots]

        # Calculate coverage and missing periods
        n = len(sorted_clean)
        first_key = keyed_snapshots[0][0]
        last_key = keyed_snapshots[-1][0]

        if isinstance(first_key, (int, float)) and isinstance(last_key, (int, float)):
            expected_count = max(int(round(last_key - first_key)) + 1, n)
        else:
            expected_count = n

        missing_periods = max(0, expected_count - n)
        coverage_ratio = n / expected_count if expected_count > 0 else 0.0

        if n < 3 or coverage_ratio < 0.50:
            temporal_quality = "INSUFFICIENT"
        elif coverage_ratio >= 0.85 and missing_periods <= 1:
            temporal_quality = "FULL"
        else:
            temporal_quality = "PARTIAL"

        first_date = str(keyed_snapshots[0][1]) if keyed_snapshots[0][1] else None
        last_date = str(keyed_snapshots[-1][1]) if keyed_snapshots[-1][1] else None

        rep = HistoricalCoverageReport(
            available_snapshots=n,
            expected_snapshots=expected_count,
            coverage_ratio=round(coverage_ratio, 4),
            missing_periods=missing_periods,
            temporal_quality=temporal_quality,
            is_chronological=is_chronological,
            has_duplicates=has_duplicates,
            date_range=(first_date, last_date),
        )

        return sorted_clean, rep

    @classmethod
    def _parse_date_to_index(cls, date_str: str) -> Optional[int]:
        """Convert YYYY-MM or MM/YYYY into monotonic month integer."""
        # Match YYYY-MM
        m1 = re.match(r"^(\d{4})[-/](\d{1,2})$", date_str)
        if m1:
            year, month = int(m1.group(1)), int(m1.group(2))
            return year * 12 + month

        # Match MM/YYYY
        m2 = re.match(r"^(\d{1,2})[-/](\d{4})$", date_str)
        if m2:
            month, year = int(m2.group(1)), int(m2.group(2))
            return year * 12 + month

        return None
