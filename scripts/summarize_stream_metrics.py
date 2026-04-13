"""Summarize stream protocol benchmark history from CSV artifacts.

Reads `tmp/metrics/stream_protocol_metrics_history.csv` and prints:
- latest sample
- rolling medians over a configurable window
- deltas vs previous and first sample

This script is intended to quickly spot performance drift over time.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class Sample:
    timestamp: str
    refresh_html_bytes: float
    v1_payload_bytes: float
    byte_savings_ratio: float
    v1_median_ms: float
    refresh_median_ms: float
    v1_to_refresh_ratio: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize stream protocol metrics history."
    )
    parser.add_argument(
        "--history",
        default="tmp/metrics/stream_protocol_metrics_history.csv",
        help="Path to the metrics history CSV file.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Rolling window size for medians.",
    )
    return parser.parse_args()


def _to_float(value: str, field: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field!r} value: {value!r}") from exc


def _row_float(row: dict[str, str], aliases: list[str], field: str) -> float:
    for alias in aliases:
        value = row.get(alias)
        if value is not None and value != "":
            return _to_float(value, field)
    raise ValueError(f"Missing {field!r} column (accepted: {', '.join(aliases)})")


def load_samples(path: Path) -> list[Sample]:
    if not path.exists():
        raise FileNotFoundError(f"Metrics history file not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        samples: list[Sample] = []
        for row in reader:
            samples.append(
                Sample(
                    timestamp=row.get("timestamp", ""),
                    refresh_html_bytes=_to_float(
                        row.get("refresh_html_bytes", ""), "refresh_html_bytes"
                    ),
                    v1_payload_bytes=_row_float(
                        row,
                        ["v1_payload_bytes", "v2_payload_bytes"],
                        "v1_payload_bytes",
                    ),
                    byte_savings_ratio=_to_float(
                        row.get("byte_savings_ratio", ""), "byte_savings_ratio"
                    ),
                    v1_median_ms=_row_float(
                        row,
                        ["v1_median_ms", "v2_median_ms"],
                        "v1_median_ms",
                    ),
                    refresh_median_ms=_to_float(
                        row.get("refresh_median_ms", ""), "refresh_median_ms"
                    ),
                    v1_to_refresh_ratio=_row_float(
                        row,
                        ["v1_to_refresh_ratio", "v2_to_refresh_ratio"],
                        "v1_to_refresh_ratio",
                    ),
                )
            )

    if not samples:
        raise ValueError(f"No metric rows found in {path}")

    return samples


def rolling_median(samples: Iterable[Sample], attr: str) -> float:
    values = [getattr(sample, attr) for sample in samples]
    return float(median(values))


def summarize(samples: list[Sample], window: int) -> str:
    window = max(1, window)
    latest = samples[-1]
    previous = samples[-2] if len(samples) > 1 else None
    baseline = samples[0]

    active = samples[-window:]
    rolling_savings = rolling_median(active, "byte_savings_ratio")
    rolling_v1_ms = rolling_median(active, "v1_median_ms")
    rolling_refresh_ms = rolling_median(active, "refresh_median_ms")
    rolling_ratio = rolling_median(active, "v1_to_refresh_ratio")

    delta_prev_savings = (
        latest.byte_savings_ratio - previous.byte_savings_ratio if previous else 0.0
    )
    delta_prev_ratio = (
        latest.v1_to_refresh_ratio - previous.v1_to_refresh_ratio if previous else 0.0
    )

    delta_base_savings = latest.byte_savings_ratio - baseline.byte_savings_ratio
    delta_base_ratio = latest.v1_to_refresh_ratio - baseline.v1_to_refresh_ratio

    lines = [
        "Stream Metrics Summary",
        f"Samples: {len(samples)}",
        f"Latest: {latest.timestamp}",
        "",
        "Latest",
        f"  Byte savings: {latest.byte_savings_ratio:.1%}",
        f"  v1 median: {latest.v1_median_ms:.2f} ms",
        f"  refresh median: {latest.refresh_median_ms:.2f} ms",
        f"  v1/refresh ratio: {latest.v1_to_refresh_ratio:.3f}",
        "",
        f"Rolling medians (last {len(active)})",
        f"  Byte savings: {rolling_savings:.1%}",
        f"  v1 median: {rolling_v1_ms:.2f} ms",
        f"  refresh median: {rolling_refresh_ms:.2f} ms",
        f"  v1/refresh ratio: {rolling_ratio:.3f}",
        "",
        "Deltas",
        f"  vs previous byte savings: {delta_prev_savings:+.2%}",
        f"  vs previous v1/refresh ratio: {delta_prev_ratio:+.3f}",
        f"  vs first byte savings: {delta_base_savings:+.2%}",
        f"  vs first v1/refresh ratio: {delta_base_ratio:+.3f}",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    path = Path(args.history)

    try:
        samples = load_samples(path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    print(summarize(samples, args.window))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
