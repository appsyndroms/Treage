from __future__ import annotations

from itertools import product
from typing import Any

from .analysis_utils import regime_rate
from .cache import ResearchCache, _tail_key
from .conditional import analyse_conditional_regime_comparison
from .derived_metrics import apply_derived_metrics
from .interaction import analyse_interaction
from .multi_regime import analyse_multi_regime_comparison
from .nested_regime import analyse_nested_regime_comparison
from .regime import analyse_regime_comparison
from .spec import ResearchSpec
from .stratified_interaction import analyse_stratified_interaction
from .stratified_regime import analyse_stratified_regime_comparison


def _analyse_tail(
    cache: ResearchCache,
    signal,
    fraction,
    target_name,
    window_name,
    split_name,
):
    signal_name = signal.name

    key = _tail_key(
        signal_name=signal_name,
        direction=signal.direction,
        fraction=fraction,
    )

    mask = cache.tail_masks[key]
    target = cache.targets[target_name]
    window_mask = cache.window_masks[
        window_name
    ][split_name]

    selected = (
        mask
        & window_mask
        & np.isfinite(target)
    )

    count = int(
        selected.sum()
    )

    if count == 0:
        return {
            "signal": signal_name,
            "direction": signal.direction,
            "fraction": fraction,
            "target": target_name,
            "window": window_name,
            "split": split_name,
            "n": 0,
            "rate": None,
        }

    return {
        "signal": signal_name,
        "direction": signal.direction,
        "fraction": fraction,
        "target": target_name,
        "window": window_name,
        "split": split_name,
        "n": count,
        "rate": float(
            np.mean(
                target[selected]
            )
        ),
    }


def run_spec(
    cache: ResearchCache,
    spec: ResearchSpec,
) -> dict[str, Any]:
    """
    Kör en research-specifikation mot en färdig ResearchCache.

    Engine känner inte till någon specifik datakälla.
    Alla domänspecifika definitioner kommer via spec och cache.
    """

    analysis_type = spec.analysis.type
    results: list[dict[str, Any]] = []

    if analysis_type == "tail":
        for signal in spec.signals:
            for fraction in signal.bins:
                for target_name in spec.targets:
                    for window_name, splits in (
                        cache.window_masks.items()
                    ):
                        for split_name in splits:
                            results.append(
                                _analyse_tail(
                                    cache=cache,
                                    signal=signal,
                                    fraction=fraction,
                                    target_name=target_name,
                                    window_name=window_name,
                                    split_name=split_name,
                                )
                            )

    elif analysis_type == "interaction":
        results = analyse_interaction(
            cache=cache,
            spec=spec,
        )

    elif analysis_type == "regime_comparison":
        results = analyse_regime_comparison(
            cache=cache,
            spec=spec,
        )

    elif analysis_type == "nested_regime_comparison":
        results = analyse_nested_regime_comparison(
            cache=cache,
            spec=spec,
        )

    elif analysis_type == "conditional_regime_comparison":
        results = analyse_conditional_regime_comparison(
            cache=cache,
            spec=spec,
        )

    elif analysis_type == "multi_regime_comparison":
        results = analyse_multi_regime_comparison(
            cache=cache,
            spec=spec,
        )

    elif analysis_type == "stratified_regime_comparison":
        results = analyse_stratified_regime_comparison(
            cache=cache,
            spec=spec,
        )

    elif analysis_type == "stratified_interaction":
        results = analyse_stratified_interaction(
            cache=cache,
            spec=spec,
        )

    else:
        raise ValueError(
            f"Okänd analysform: {analysis_type}"
        )

    results = apply_derived_metrics(
        spec,
        results,
    )

    return {
        "spec_id": spec.id,
        "question": spec.question,
        "mode": spec.mode,
        "analysis": analysis_type,
        "results": results,
    }
