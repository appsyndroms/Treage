from __future__ import annotations
from itertools import product
from typing import Any, Callable
from .analysis_utils import regime_rate
from .cache import ResearchCache, _tail_key
from .conditional import (
    analyse_conditional_regime_comparison,
)
from .derived_metrics import apply_derived_metrics
from .interaction import analyse_interaction
from .multi_regime import analyse_multi_regime_comparison
from .nested_regime import analyse_nested_regime_comparison
from .regime import analyse_regime_comparison
from .spec import ResearchSpec, SignalSpec
from .stratified_interaction import (
    analyse_stratified_interaction,
)
from .stratified_regime import (
    analyse_stratified_regime_comparison,
)
AnalysisFunction = Callable[..., list[dict[str, Any]]]
def _analyse_tail(
    cache: ResearchCache,
    signal: SignalSpec,
    fraction: float,
    target_name: str,
    window_name: str,
    split_name: str,
) -> dict[str, Any]:
    target = cache.targets[
        target_name
    ]
    window_mask = cache.window_masks[
        window_name
    ][split_name]
    tail_mask = cache.tail_masks[
        _tail_key(
            signal.name,
            signal.direction,
            fraction,
        )
    ]
    mask = (
        window_mask
        & tail_mask
    )
    metrics = regime_rate(
        target,
        mask,
    )
    return {
        "analysis": "tail",
        "signal": signal.name,
        "direction": signal.direction,
        "fraction": fraction,
        "target": target_name,
        "window": window_name,
        "split": split_name,
        "n": metrics["n"],
        "events": metrics["events"],
        "event_rate": metrics["event_rate"],
    }
def _fractions(
    signals: tuple[SignalSpec, ...],
) -> tuple[float, ...]:
    return tuple(
        signal.bins[0]
        for signal in signals
    )
def _run_standard_analysis(
    cache: ResearchCache,
    spec: ResearchSpec,
    analyser: AnalysisFunction,
    *,
    fractions: tuple[float, ...],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    bootstrap = spec.analysis.bootstrap
    bootstrap_iterations = (
        spec.analysis.bootstrap_iterations
    )
    for target_name in spec.targets:
        for window_name in spec.windows:
            for split_name in spec.splits:
                results.extend(
                    analyser(
                        cache,
                        spec.signals,
                        target_name,
                        fractions,
                        window_name,
                        split_name,
                        bootstrap=bootstrap,
                        bootstrap_iterations=(
                            bootstrap_iterations
                        ),
                        spec_id=spec.id,
                    )
                    if isinstance(
                        analyser,
                        type(
                            analyse_stratified_regime_comparison
                        ),
                    )
                    else []
                )
    return results
def _run_fixed_fraction_analysis(
    cache: ResearchCache,
    spec: ResearchSpec,
    analyser: Callable[..., list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    fractions = _fractions(
        spec.signals
    )
    results: list[dict[str, Any]] = []
    for target_name in spec.targets:
        for window_name in spec.windows:
            for split_name in spec.splits:
                results.extend(
                    analyser(
                        cache,
                        spec.signals,
                        target_name,
                        fractions,
                        window_name,
                        split_name,
                        bootstrap=spec.analysis.bootstrap,
                        bootstrap_iterations=(
                            spec.analysis
                            .bootstrap_iterations
                        ),
                        spec_id=spec.id,
                    )
                )
    return results
def _run_conditional_analysis(
    cache: ResearchCache,
    spec: ResearchSpec,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    baseline_fraction_options = [
        signal.bins
        for signal in spec.signals[:-1]
    ]
    for baseline_fractions in product(
        *baseline_fraction_options
    ):
        for incremental_fraction in (
            spec.signals[-1].bins
        ):
            fractions = (
                *baseline_fractions,
                incremental_fraction,
            )
            for target_name in spec.targets:
                for window_name in spec.windows:
                    for split_name in spec.splits:
                        results.append(
                            analyse_conditional_regime_comparison(
                                cache,
                                spec.signals,
                                target_name,
                                fractions,
                                window_name,
                                split_name,
                                bootstrap=(
                                    spec.analysis.bootstrap
                                ),
                                bootstrap_iterations=(
                                    spec.analysis
                                    .bootstrap_iterations
                                ),
                                spec_id=spec.id,
                            )
                        )
    return results
def _run_stratified_interaction(
    cache: ResearchCache,
    spec: ResearchSpec,
) -> list[dict[str, Any]]:
    fractions = _fractions(
        spec.signals
    )
    results: list[dict[str, Any]] = []
    for target_name in spec.targets:
        for window_name in spec.windows:
            for split_name in spec.splits:
                results.extend(
                    analyse_stratified_interaction(
                        cache,
                        spec.signals,
                        target_name,
                        fractions,
                        window_name,
                        split_name,
                        bootstrap=spec.analysis.bootstrap,
                        bootstrap_iterations=(
                            spec.analysis
                            .bootstrap_iterations
                        ),
                        spec_id=spec.id,
                        rules=spec.analysis.rules,
                    )
                )
    return results
def _run_analysis(
    cache: ResearchCache,
    spec: ResearchSpec,
) -> list[dict[str, Any]]:
    analysis_type = spec.analysis.type
    fixed_fraction_analysers = {
        "interaction": analyse_interaction,
        "regime_comparison": (
            analyse_regime_comparison
        ),
        "nested_regime_comparison": (
            analyse_nested_regime_comparison
        ),
        "multi_regime_comparison": (
            analyse_multi_regime_comparison
        ),
        "stratified_regime_comparison": (
            analyse_stratified_regime_comparison
        ),
    }
    analyser = fixed_fraction_analysers.get(
        analysis_type
    )
    if analyser is not None:
        return _run_fixed_fraction_analysis(
            cache,
            spec,
            analyser,
        )
    if analysis_type == (
        "conditional_regime_comparison"
    ):
        return _run_conditional_analysis(
            cache,
            spec,
        )
    if analysis_type == (
        "stratified_interaction"
    ):
        return _run_stratified_interaction(
            cache,
            spec,
        )
    raise ValueError(
        f"Unsupported analysis type: "
        f"{analysis_type}"
    )
def run_spec(
    cache: ResearchCache,
    spec: ResearchSpec,
) -> dict[str, Any]:
    if spec.analysis.type == "tail":
        results: list[dict[str, Any]] = []
        for signal in spec.signals:
            for fraction in signal.bins:
                for target_name in spec.targets:
                    for window_name in spec.windows:
                        for split_name in spec.splits:
                            results.append(
                                _analyse_tail(
                                    cache,
                                    signal,
                                    fraction,
                                    target_name,
                                    window_name,
                                    split_name,
                                )
                            )
    else:
        results = _run_analysis(
            cache,
            spec,
        )
    results = apply_derived_metrics(
        spec,
        results,
    )
    return {
        "spec_id": spec.id,
        "question": spec.question,
        "mode": spec.mode,
        "analysis": spec.analysis.type,
        "results": results,
    }
