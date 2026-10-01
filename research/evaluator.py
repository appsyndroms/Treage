from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .bootstrap import bootstrap_mean_ci
from .cache import ResearchCache, _tail_key
from .spec import SignalSpec


def _stable_seed(
    *parts: object,
) -> int:
    payload = "|".join(
        str(part)
        for part in parts
    ).encode("utf-8")

    digest = hashlib.sha256(
        payload
    ).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="little",
        signed=False,
    ) % (2**32 - 1)


def _safe_auc(
    y_true: np.ndarray,
    scores: np.ndarray,
) -> float | None:
    valid = (
        np.isfinite(y_true)
        & np.isfinite(scores)
    )

    if not np.any(valid):
        return None

    y = y_true[valid]
    s = scores[valid]

    if np.unique(y).size < 2:
        return None

    try:
        return float(
            roc_auc_score(y, s)
        )
    except ValueError:
        return None


def _binary_metrics(
    target: np.ndarray,
    selected: np.ndarray,
) -> dict[str, Any]:
    valid = np.isfinite(target)

    if not np.any(valid):
        return {
            "n": 0,
            "events": 0,
            "event_rate": None,
            "baseline_event_rate": None,
            "lift": None,
        }

    y = target[valid].astype(float)
    selection = selected[valid]

    events = y > 0

    n = int(selection.sum())

    selected_events = int(
        events[selection].sum()
    )

    baseline_rate = float(
        events.mean()
    )

    if n == 0:
        return {
            "n": 0,
            "events": 0,
            "event_rate": None,
            "baseline_event_rate": baseline_rate,
            "lift": None,
        }

    event_rate = (
        selected_events / n
    )

    lift = (
        event_rate / baseline_rate
        if baseline_rate > 0
        else None
    )

    return {
        "n": n,
        "events": selected_events,
        "event_rate": float(event_rate),
        "baseline_event_rate": baseline_rate,
        "lift": (
            float(lift)
            if lift is not None
            else None
        ),
    }


def _return_metrics(
    returns: np.ndarray | None,
    selected: np.ndarray,
    *,
    seed: int,
) -> dict[str, Any]:
    if returns is None:
        return {
            "return_n": 0,
            "mean_return": None,
            "median_return": None,
            "bootstrap_ci_low": None,
            "bootstrap_ci_high": None,
        }

    valid = (
        np.isfinite(returns)
        & selected
    )

    values = returns[valid]

    if values.size == 0:
        return {
            "return_n": 0,
            "mean_return": None,
            "median_return": None,
            "bootstrap_ci_low": None,
            "bootstrap_ci_high": None,
        }

    mean_return = float(
        np.mean(values)
    )

    median_return = float(
        np.median(values)
    )

    ci_low, ci_high = bootstrap_mean_ci(
        values,
        seed=seed,
    )

    return {
        "return_n": int(values.size),
        "mean_return": mean_return,
        "median_return": median_return,
        "bootstrap_ci_low": (
            float(ci_low)
            if ci_low is not None
            else None
        ),
        "bootstrap_ci_high": (
            float(ci_high)
            if ci_high is not None
            else None
        ),
    }


def _return_metrics_without_bootstrap(
    returns: np.ndarray | None,
    selected: np.ndarray,
) -> dict[str, Any]:
    if returns is None:
        return {
            "return_n": 0,
            "mean_return": None,
            "median_return": None,
            "bootstrap_ci_low": None,
            "bootstrap_ci_high": None,
        }

    valid = (
        np.isfinite(returns)
        & selected
    )

    values = returns[valid]

    if values.size == 0:
        return {
            "return_n": 0,
            "mean_return": None,
            "median_return": None,
            "bootstrap_ci_low": None,
            "bootstrap_ci_high": None,
        }

    return {
        "return_n": int(values.size),
        "mean_return": float(
            np.mean(values)
        ),
        "median_return": float(
            np.median(values)
        ),
        "bootstrap_ci_low": None,
        "bootstrap_ci_high": None,
    }


def evaluate_signal(
    frame: pd.DataFrame,
    cache: ResearchCache,
    signal: SignalSpec,
    target_name: str,
    fraction: float,
    window_name: str,
    split_name: str,
    *,
    bootstrap: bool = True,
    evaluation_id: str | None = None,
) -> dict[str, Any]:
    signal_values = cache.signals[
        signal.name
    ]

    target = cache.targets[
        target_name
    ]

    window_mask = cache.window_masks[
        window_name
    ][split_name]

    tail_key = _tail_key(
        signal.name,
        signal.direction,
        fraction,
    )

    selected = cache.tail_masks[
        tail_key
    ]

    mask = (
        window_mask
        & selected
        & np.isfinite(signal_values)
        & np.isfinite(target)
    )

    target_config = cache.target_configs[
        target_name
    ]

    return_column = getattr(
        target_config,
        "return_column",
        None,
    )

    returns = (
        cache.returns.get(return_column)
        if return_column
        else None
    )

    auc_mask = (
        window_mask
        & np.isfinite(signal_values)
        & np.isfinite(target)
    )

    auc = _safe_auc(
        target[auc_mask],
        signal_values[auc_mask],
    )

    binary = _binary_metrics(
        target[window_mask],
        selected[window_mask],
    )

    if bootstrap:
        seed = _stable_seed(
            evaluation_id or signal.name,
            target_name,
            fraction,
            signal.direction,
            window_name,
            split_name,
        )

        returns_metrics = _return_metrics(
            returns,
            window_mask & selected,
            seed=seed,
        )
    else:
        returns_metrics = (
            _return_metrics_without_bootstrap(
                returns,
                window_mask & selected,
            )
        )

    result: dict[str, Any] = {
        "signal_name": signal.name,
        "target_name": target_name,
        "fraction": fraction,
        "direction": signal.direction,
        "window": window_name,
        "split": split_name,
        "auc": auc,
        **binary,
        **returns_metrics,
    }

    result["n_valid_auc"] = int(
        auc_mask.sum()
    )

    result["n_valid_target"] = int(
        np.isfinite(
            target[window_mask]
        ).sum()
    )

    result["selected_fraction"] = (
        float(
            selected[window_mask].mean()
        )
        if window_mask.any()
        else None
    )

    result["n_valid"] = int(
        mask.sum()
    )

    return result
