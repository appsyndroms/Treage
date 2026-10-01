from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any


def _numeric_values(
    rows: list[dict[str, Any]],
    field: str,
) -> list[float]:
    values: list[float] = []

    for row in rows:
        value = row.get(field)

        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            values.append(float(value))

    return values


def _summarize_field(
    rows: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:
    values = _numeric_values(rows, field)

    if not values:
        return {
            "n": 0,
            "mean": None,
            "min": None,
            "max": None,
        }

    return {
        "n": len(values),
        "mean": mean(values),
        "min": min(values),
        "max": max(values),
    }


def _sign_consistency(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "n": 0,
            "positive": 0,
            "negative": 0,
            "zero": 0,
            "consistent": False,
        }

    positive = sum(value > 0 for value in values)
    negative = sum(value < 0 for value in values)
    zero = sum(value == 0 for value in values)

    return {
        "n": len(values),
        "positive": positive,
        "negative": negative,
        "zero": zero,
        "consistent": (
            positive == len(values)
            or negative == len(values)
        ),
    }


def _threshold_consistency(
    values: list[float],
    baseline: float,
) -> dict[str, Any]:
    if not values:
        return {
            "n": 0,
            "baseline": baseline,
            "above": 0,
            "below": 0,
            "equal": 0,
            "consistent": False,
        }

    above = sum(value > baseline for value in values)
    below = sum(value < baseline for value in values)
    equal = sum(value == baseline for value in values)

    return {
        "n": len(values),
        "baseline": baseline,
        "above": above,
        "below": below,
        "equal": equal,
        "consistent": (
            above == len(values)
            or below == len(values)
        ),
    }


def _stability(
    values: list[float],
    definition: dict[str, Any],
) -> dict[str, Any] | None:
    stability_type = definition.get("stability")

    if stability_type in (None, "none"):
        return None

    if stability_type == "sign":
        return _sign_consistency(values)

    if stability_type == "threshold":
        if "baseline" not in definition:
            raise ValueError(
                "Threshold stability requires a baseline."
            )

        return _threshold_consistency(
            values,
            float(definition["baseline"]),
        )

    raise ValueError(
        f"Unsupported stability type: {stability_type}"
    )


def _window_metric_means(
    windows: list[dict[str, Any]],
    field: str,
) -> list[float]:
    values: list[float] = []

    for window in windows:
        summary = window.get("metrics", {}).get(field, {})
        value = summary.get("mean")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))

    return values


def _cross_window_stability(
    windows: list[dict[str, Any]],
    metric_definitions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    stability: dict[str, Any] = {}

    for field, definition in metric_definitions.items():
        if definition.get("stability") != "threshold":
            continue

        if "baseline" not in definition:
            raise ValueError(
                f"Threshold stability requires a baseline for '{field}'."
            )

        values = _window_metric_means(windows, field)

        stability[field] = _threshold_consistency(
            values,
            float(definition["baseline"]),
        )

    return stability


def aggregate_walk_forward(
    results: list[dict[str, Any]],
    *,
    metric_definitions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

    for result in results:
        window = result.get("window", {})
        window_name = window.get("name")

        if window_name is None:
            raise ValueError(
                "Walk-forward result is missing window.name."
            )

        grouped[str(window_name)].append(result)

    windows: list[dict[str, Any]] = []

    for window_name, rows in grouped.items():
        metrics: dict[str, Any] = {}
        stability: dict[str, Any] = {}

        for field, definition in metric_definitions.items():
            metrics[field] = _summarize_field(rows, field)

            values = _numeric_values(rows, field)
            metric_stability = _stability(values, definition)

            if metric_stability is not None:
                stability[field] = metric_stability

        windows.append(
            {
                "name": window_name,
                "result_count": len(rows),
                "metrics": metrics,
                "stability": stability,
            }
        )

    windows.sort(key=lambda window: window["name"])

    overall_metrics: dict[str, Any] = {}

    for field in metric_definitions:
        overall_metrics[field] = _summarize_field(results, field)

    return {
        "window_count": len(windows),
        "result_count": len(results),
        "windows": windows,
        "overall": {
            "metrics": overall_metrics,
            "baseline_consistency": _cross_window_stability(
                windows,
                metric_definitions,
            ),
        },
    }
