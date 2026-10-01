from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..features.dataset import FeatureDataset
from ..outcomes.registry import TargetDefinition, TargetRegistry
from ..outcomes.targets import build_target
from .signals import build_signal, tail_mask


@dataclass(frozen=True)
class ResearchRequirement:
    signal_name: str
    target_name: str
    tail_fraction: float
    tail_direction: str


@dataclass
class ResearchCache:
    signals: dict[str, np.ndarray]
    targets: dict[str, np.ndarray]
    target_configs: dict[str, TargetDefinition]
    returns: dict[str, np.ndarray]
    tail_masks: dict[str, np.ndarray]
    window_masks: dict[str, dict[str, np.ndarray]]


def _build_window_masks(
    frame: pd.DataFrame,
    windows,
) -> dict[str, dict[str, np.ndarray]]:
    """Bygger train/validation/test-masker för varje walk-forward-fönster."""

    dates = pd.to_datetime(
        frame["snapshot_date"],
        errors="coerce",
    )

    result: dict[
        str,
        dict[str, np.ndarray],
    ] = {}

    for index, window in enumerate(
        windows,
        start=1,
    ):
        train_end = pd.Timestamp(
            window.train_end
        )
        validation_end = pd.Timestamp(
            window.validation_end
        )
        test_end = pd.Timestamp(
            window.test_end
        )

        result[f"window_{index}"] = {
            "train": (
                dates <= train_end
            ).to_numpy(),
            "validation": (
                (dates > train_end)
                & (dates <= validation_end)
            ).to_numpy(),
            "test": (
                (dates > validation_end)
                & (dates <= test_end)
            ).to_numpy(),
        }

    return result


def _tail_key(
    signal_name: str,
    direction: str,
    fraction: float,
) -> str:
    return (
        f"{signal_name}|"
        f"{direction}|"
        f"{fraction}"
    )


def build_research_cache(
    dataset: FeatureDataset,
    requirements: list[ResearchRequirement],
    target_registry: TargetRegistry,
    windows,
) -> ResearchCache:
    """
    Bygger ett cache-lager för en research-session.

    Cachen innehåller bara sådant som faktiskt krävs av
    de research-specifikationer som ska köras.
    """

    frame = dataset.frame
    signal_registry = dataset.registry

    signals: dict[str, np.ndarray] = {}
    targets: dict[str, np.ndarray] = {}
    target_configs: dict[
        str,
        TargetDefinition,
    ] = {}
    returns: dict[str, np.ndarray] = {}
    tail_masks: dict[str, np.ndarray] = {}

    required_signal_names = {
        requirement.signal_name
        for requirement in requirements
    }

    required_target_names = {
        requirement.target_name
        for requirement in requirements
    }

    for signal_name in required_signal_names:
        signal = build_signal(
            frame=frame,
            signal_name=signal_name,
            registry=signal_registry,
        )

        signals[signal_name] = signal.to_numpy(
            dtype=np.float64
        )

    for target_name in required_target_names:
        target_config = target_registry.get(
            target_name
        )

        target_registry.validate_frame(
            frame,
            target_name,
        )

        target_configs[target_name] = target_config

        target = build_target(
            frame,
            target_config,
        )

        targets[target_name] = target.to_numpy(
            dtype=np.float64
        )

        return_column = target_config.return_column

        if return_column not in returns:
            if return_column not in frame.columns:
                raise ValueError(
                    f"Saknar return-kolumn: {return_column}"
                )

            returns[return_column] = (
                pd.to_numeric(
                    frame[return_column],
                    errors="coerce",
                )
                .replace(
                    [np.inf, -np.inf],
                    np.nan,
                )
                .to_numpy(
                    dtype=np.float64
                )
            )

    for requirement in requirements:
        signal = pd.Series(
            signals[requirement.signal_name],
            index=frame.index,
        )

        mask = tail_mask(
            frame=frame,
            signal=signal,
            fraction=requirement.tail_fraction,
            direction=requirement.tail_direction,
        )

        key = _tail_key(
            signal_name=requirement.signal_name,
            direction=requirement.tail_direction,
            fraction=requirement.tail_fraction,
        )

        tail_masks[key] = mask.to_numpy(
            dtype=bool
        )

    window_masks = _build_window_masks(
        frame,
        windows,
    )

    return ResearchCache(
        signals=signals,
        targets=targets,
        target_configs=target_configs,
        returns=returns,
        tail_masks=tail_masks,
        window_masks=window_masks,
    )
