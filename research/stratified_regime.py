from __future__ import annotations
from typing import Any
from .analysis_utils import regime_rate, stable_seed
from .bootstrap import (
    bootstrap_binary_rate_difference_between_groups,
)
from .cache import ResearchCache, _tail_key
from .spec import SignalSpec
def _build_disjoint_bands(
    cache: ResearchCache,
    signal: SignalSpec,
) -> list[tuple[str, float, float, Any]]:
    """
    Bygger disjunkta percentileband från signalens kumulativa
    tail-masker.
    Banden representerar successiva intervall av tail-storlek.
    Exempel för bins [0.20, 0.50, 1.00]:
        0.00-0.20
        0.20-0.50
        0.50-1.00
    För lower betyder 0.00-0.20 den lägsta 20 procenten.
    För upper betyder 0.00-0.20 den högsta 20 procenten.
    Den interna representationen använder alltid tail-storlek
    snarare än absolut percentile-riktning. Det viktiga är att
    banden är disjunkta.
    """
    fractions = tuple(sorted(signal.bins))
    bands: list[
        tuple[str, float, float, Any]
    ] = []
    previous = 0.0
    for fraction in fractions:
        current_mask = cache.tail_masks[
            _tail_key(
                signal.name,
                signal.direction,
                fraction,
            )
        ]
        if previous == 0.0:
            band_mask = current_mask.copy()
        else:
            previous_mask = cache.tail_masks[
                _tail_key(
                    signal.name,
                    signal.direction,
                    previous,
                )
            ]
            band_mask = (
                current_mask
                & ~previous_mask
            )
        label = (
            f"{signal.direction}_"
            f"{previous:g}_{fraction:g}"
        )
        bands.append(
            (
                label,
                previous,
                fraction,
                band_mask,
            )
        )
        previous = fraction
    return bands
def analyse_stratified_regime_comparison(
    cache: ResearchCache,
    signals: tuple[SignalSpec, ...],
    target_name: str,
    fractions: tuple[float, ...],
    window_name: str,
    split_name: str,
    *,
    bootstrap: bool,
    bootstrap_iterations: int,
    spec_id: str,
) -> list[dict[str, Any]]:
    """
    Testar om den sista signalen tillför information efter att
    styrkan i de två första signalerna redan har kontrollerats.
    De två första signalerna delas upp i disjunkta styrkeband.
    Varje kombination av band bildar ett separat stratum.
    Inom varje stratum jämförs:
        tredje signalens tail
        mot
        resten av observationerna i stratumat.
    På så sätt testas om den tredje signalen tillför information
    utöver de två första signalernas nivåer.
    """
    if len(signals) != 3:
        raise ValueError(
            "stratified_regime_comparison kräver "
            "exakt tre signaler."
        )
    if len(signals) != len(fractions):
        raise ValueError(
            "Number of signals must match "
            "number of fractions."
        )
    if len(signals[0].bins) < 3:
        raise ValueError(
            "Den första signalen måste ha minst "
            "tre bins för stratifiering."
        )
    if len(signals[1].bins) < 3:
        raise ValueError(
            "Den andra signalen måste ha minst "
            "tre bins för stratifiering."
        )
    target = cache.targets[target_name]
    window_mask = cache.window_masks[
        window_name
    ][split_name]
    first_bands = _build_disjoint_bands(
        cache,
        signals[0],
    )
    second_bands = _build_disjoint_bands(
        cache,
        signals[1],
    )
    incremental_fraction = fractions[2]
    incremental_mask = cache.tail_masks[
        _tail_key(
            signals[2].name,
            signals[2].direction,
            incremental_fraction,
        )
    ]
    results: list[dict[str, Any]] = []
    for (
        first_label,
        first_lower,
        first_upper,
        first_mask,
    ) in first_bands:
        for (
            second_label,
            second_lower,
            second_upper,
            second_mask,
        ) in second_bands:
            stratum_mask = (
                first_mask
                & second_mask
            )
            incremental_in_stratum = (
                stratum_mask
                & incremental_mask
            )
            comparator_in_stratum = (
                stratum_mask
                & ~incremental_mask
            )
            baseline_in_window = (
                stratum_mask
                & window_mask
            )
            incremental_in_window = (
                incremental_in_stratum
                & window_mask
            )
            comparator_in_window = (
                comparator_in_stratum
                & window_mask
            )
            baseline_metrics = regime_rate(
                target,
                baseline_in_window,
            )
            incremental_metrics = regime_rate(
                target,
                incremental_in_window,
            )
            comparator_metrics = regime_rate(
                target,
                comparator_in_window,
            )
            incremental_rate = (
                incremental_metrics["event_rate"]
            )
            comparator_rate = (
                comparator_metrics["event_rate"]
            )
            absolute_difference = None
            if (
                incremental_rate is not None
                and comparator_rate is not None
            ):
                absolute_difference = (
                    incremental_rate
                    - comparator_rate
                )
            lift = None
            if (
                comparator_rate is not None
                and comparator_rate > 0
                and incremental_rate is not None
            ):
                lift = (
                    incremental_rate
                    / comparator_rate
                )
            ci_low = None
            ci_high = None
            if bootstrap:
                seed = stable_seed(
                    spec_id,
                    signals[0].name,
                    signals[1].name,
                    signals[2].name,
                    first_lower,
                    first_upper,
                    second_lower,
                    second_upper,
                    incremental_fraction,
                    target_name,
                    window_name,
                    split_name,
                )
                (
                    ci_low,
                    ci_high,
                ) = (
                    bootstrap_binary_rate_difference_between_groups(
                        target[window_mask],
                        comparator_in_stratum[
                            window_mask
                        ],
                        incremental_in_stratum[
                            window_mask
                        ],
                        iterations=(
                            bootstrap_iterations
                        ),
                        seed=seed,
                    )
                )
            results.append(
                {
                    "analysis": (
                        "stratified_regime_comparison"
                    ),
                    "target": target_name,
                    "window": window_name,
                    "split": split_name,
                    "stratum": (
                        f"{first_label}__"
                        f"{second_label}"
                    ),
                    "signal_1_band": first_label,
                    "signal_1_lower": first_lower,
                    "signal_1_upper": first_upper,
                    "signal_2_band": second_label,
                    "signal_2_lower": second_lower,
                    "signal_2_upper": second_upper,
                    "incremental_signal": (
                        signals[2].name
                    ),
                    "incremental_direction": (
                        signals[2].direction
                    ),
                    "incremental_fraction": (
                        incremental_fraction
                    ),
                    "baseline_n": (
                        baseline_metrics["n"]
                    ),
                    "baseline_events": (
                        baseline_metrics["events"]
                    ),
                    "baseline_event_rate": (
                        baseline_metrics["event_rate"]
                    ),
                    "incremental_n": (
                        incremental_metrics["n"]
                    ),
                    "incremental_events": (
                        incremental_metrics["events"]
                    ),
                    "incremental_event_rate": (
                        incremental_rate
                    ),
                    "comparator_n": (
                        comparator_metrics["n"]
                    ),
                    "comparator_events": (
                        comparator_metrics["events"]
                    ),
                    "comparator_event_rate": (
                        comparator_rate
                    ),
                    "absolute_event_rate_difference": (
                        absolute_difference
                    ),
                    "lift": lift,
                    "bootstrap_ci_low": ci_low,
                    "bootstrap_ci_high": ci_high,
                }
            )
    return results
