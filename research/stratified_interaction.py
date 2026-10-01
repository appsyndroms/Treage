from __future__ import annotations

from typing import Any

import numpy as np

from .analysis_utils import stable_seed
from .bootstrap import (
    bootstrap_binary_rate_difference_in_differences,
)
from .cache import ResearchCache, _tail_key
from .spec import SignalSpec


def _build_disjoint_bands(
    cache: ResearchCache,
    signal: SignalSpec,
) -> list[tuple[str, float, float, np.ndarray]]:
    fractions = tuple(sorted(signal.bins))
    bands = []
    previous = 0.0

    for fraction in fractions:
        current = cache.tail_masks[
            _tail_key(
                signal.name,
                signal.direction,
                fraction,
            )
        ]

        if previous == 0.0:
            mask = current.copy()
        else:
            previous_mask = cache.tail_masks[
                _tail_key(
                    signal.name,
                    signal.direction,
                    previous,
                )
            ]

            mask = current & ~previous_mask

        bands.append(
            (
                f"{signal.direction}_{previous:g}_{fraction:g}",
                previous,
                fraction,
                mask,
            )
        )

        previous = fraction

    return bands


def _rate(
    target: np.ndarray,
    mask: np.ndarray,
) -> tuple[int, int, float | None]:
    selected = target[mask]
    n = int(selected.shape[0])

    if n == 0:
        return 0, 0, None

    events = int(
        (selected > 0).sum()
    )

    return n, events, events / n


def _interaction_effect(
    target: np.ndarray,
    stratum_mask: np.ndarray,
    test_mask: np.ndarray,
    window_mask: np.ndarray,
) -> dict[str, Any]:
    selected = (
        stratum_mask
        & test_mask
        & window_mask
    )

    reference = (
        stratum_mask
        & ~test_mask
        & window_mask
    )

    selected_n, selected_events, selected_rate = _rate(
        target,
        selected,
    )

    reference_n, reference_events, reference_rate = _rate(
        target,
        reference,
    )

    effect = None

    if (
        selected_rate is not None
        and reference_rate is not None
    ):
        effect = (
            selected_rate
            - reference_rate
        )

    return {
        "selected_n": selected_n,
        "selected_events": selected_events,
        "selected_rate": selected_rate,
        "reference_n": reference_n,
        "reference_events": reference_events,
        "reference_rate": reference_rate,
        "interaction_effect": effect,
        "selected_mask": selected,
        "reference_mask": reference,
    }


def _contrast_row(
    target: np.ndarray,
    window_mask: np.ndarray,
    spec_id: str,
    target_name: str,
    window_name: str,
    split_name: str,
    *,
    contrast_type: str,
    reference_label: str,
    comparison_label: str,
    reference: dict[str, Any],
    comparison: dict[str, Any],
    bootstrap: bool,
    bootstrap_iterations: int,
) -> dict[str, Any]:
    reference_effect = reference[
        "interaction_effect"
    ]

    comparison_effect = comparison[
        "interaction_effect"
    ]

    difference = None

    if (
        reference_effect is not None
        and comparison_effect is not None
    ):
        difference = (
            comparison_effect
            - reference_effect
        )

    ci_low = None
    ci_high = None

    if bootstrap:
        seed = stable_seed(
            spec_id,
            target_name,
            window_name,
            split_name,
            contrast_type,
            reference_label,
            comparison_label,
        )

        ci_low, ci_high = (
            bootstrap_binary_rate_difference_in_differences(
                target[window_mask],
                reference["selected_mask"][
                    window_mask
                ],
                reference["reference_mask"][
                    window_mask
                ],
                comparison["selected_mask"][
                    window_mask
                ],
                comparison["reference_mask"][
                    window_mask
                ],
                iterations=bootstrap_iterations,
                seed=seed,
            )
        )

    return {
        "analysis": "stratified_interaction",
        "target": target_name,
        "window": window_name,
        "split": split_name,
        "contrast_type": contrast_type,
        "reference_stratum": reference_label,
        "comparison_stratum": comparison_label,
        "reference_interaction_effect": reference_effect,
        "comparison_interaction_effect": comparison_effect,
        "interaction_difference_in_differences": difference,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "reference_selected_n": reference[
            "selected_n"
        ],
        "reference_selected_events": reference[
            "selected_events"
        ],
        "reference_selected_rate": reference[
            "selected_rate"
        ],
        "reference_reference_n": reference[
            "reference_n"
        ],
        "reference_reference_events": reference[
            "reference_events"
        ],
        "reference_reference_rate": reference[
            "reference_rate"
        ],
        "comparison_selected_n": comparison[
            "selected_n"
        ],
        "comparison_selected_events": comparison[
            "selected_events"
        ],
        "comparison_selected_rate": comparison[
            "selected_rate"
        ],
        "comparison_reference_n": comparison[
            "reference_n"
        ],
        "comparison_reference_events": comparison[
            "reference_events"
        ],
        "comparison_reference_rate": comparison[
            "reference_rate"
        ],
    }


def analyse_stratified_interaction(
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
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generic stratified interaction analysis.

    The first two signals define the stratification dimensions.
    The third signal is the condition whose effect is measured
    within each two-dimensional stratum.

    The comparison strategy is defined by the research registry.
    """

    if len(signals) != 3 or len(fractions) != 3:
        raise ValueError(
            "stratified_interaction kräver exakt tre signaler."
        )

    stratification_signals = int(
        rules.get(
            "stratification_signals",
            0,
        )
    )

    test_signal = int(
        rules.get(
            "test_signal",
            0,
        )
    )

    if stratification_signals != 2:
        raise ValueError(
            "stratified_interaction kräver två "
            "stratifieringssignaler."
        )

    if test_signal != 3:
        raise ValueError(
            "stratified_interaction kräver den tredje "
            "signalen som testsignal."
        )

    comparison = rules.get(
        "comparison"
    )

    if comparison != "outer_bands":
        raise ValueError(
            "stratified_interaction stöder endast "
            "comparison='outer_bands'."
        )

    minimum_bins = int(
        rules.get(
            "minimum_bins_per_stratification_signal",
            0,
        )
    )

    if minimum_bins < 1:
        raise ValueError(
            "stratified_interaction saknar giltigt "
            "minimum_bins_per_stratification_signal."
        )

    if (
        len(signals[0].bins) < minimum_bins
        or len(signals[1].bins) < minimum_bins
    ):
        raise ValueError(
            "De två stratifieringssignalerna måste ha "
            f"minst {minimum_bins} bins."
        )

    target = cache.targets[
        target_name
    ]

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

    test_mask = cache.tail_masks[
        _tail_key(
            signals[2].name,
            signals[2].direction,
            fractions[2],
        )
    ]

    cells: dict[
        tuple[int, int],
        dict[str, Any],
    ] = {}

    for i, (
        _,
        _,
        _,
        first_mask,
    ) in enumerate(first_bands):
        for j, (
            _,
            _,
            _,
            second_mask,
        ) in enumerate(second_bands):
            cells[(i, j)] = _interaction_effect(
                target,
                first_mask & second_mask,
                test_mask,
                window_mask,
            )

    results: list[dict[str, Any]] = []

    strong_i = 0
    weak_i = len(first_bands) - 1

    strong_j = 0
    weak_j = len(second_bands) - 1

    first_name = signals[0].name
    second_name = signals[1].name

    for j, (
        second_band_label,
        _,
        _,
        _,
    ) in enumerate(second_bands):
        reference = cells[
            (strong_i, j)
        ]

        comparison_cell = cells[
            (weak_i, j)
        ]

        results.append(
            _contrast_row(
                target,
                window_mask,
                spec_id,
                target_name,
                window_name,
                split_name,
                contrast_type=(
                    f"{first_name}_weak_vs_strong"
                ),
                reference_label=(
                    f"{first_bands[strong_i][0]}"
                    f"__{second_band_label}"
                ),
                comparison_label=(
                    f"{first_bands[weak_i][0]}"
                    f"__{second_band_label}"
                ),
                reference=reference,
                comparison=comparison_cell,
                bootstrap=bootstrap,
                bootstrap_iterations=(
                    bootstrap_iterations
                ),
            )
        )

    for i, (
        first_band_label,
        _,
        _,
        _,
    ) in enumerate(first_bands):
        reference = cells[
            (i, strong_j)
        ]

        comparison_cell = cells[
            (i, weak_j)
        ]

        results.append(
            _contrast_row(
                target,
                window_mask,
                spec_id,
                target_name,
                window_name,
                split_name,
                contrast_type=(
                    f"{second_name}_weak_vs_strong"
                ),
                reference_label=(
                    f"{first_band_label}"
                    f"__{second_bands[strong_j][0]}"
                ),
                comparison_label=(
                    f"{first_band_label}"
                    f"__{second_bands[weak_j][0]}"
                ),
                reference=reference,
                comparison=comparison_cell,
                bootstrap=bootstrap,
                bootstrap_iterations=(
                    bootstrap_iterations
                ),
            )
        )

    reference = cells[
        (strong_i, strong_j)
    ]

    comparison_cell = cells[
        (weak_i, weak_j)
    ]

    results.append(
        _contrast_row(
            target,
            window_mask,
            spec_id,
            target_name,
            window_name,
            split_name,
            contrast_type="joint_weak_vs_strong",
            reference_label=(
                f"{first_bands[strong_i][0]}"
                f"__{second_bands[strong_j][0]}"
            ),
            comparison_label=(
                f"{first_bands[weak_i][0]}"
                f"__{second_bands[weak_j][0]}"
            ),
            reference=reference,
            comparison=comparison_cell,
            bootstrap=bootstrap,
            bootstrap_iterations=(
                bootstrap_iterations
            ),
        )
    )

    return results
