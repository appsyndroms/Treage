"""Bygger forskningsutfall från observerade marknadsdata."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .registry import TargetDefinition


def build_target(
    frame: pd.DataFrame,
    target: TargetDefinition,
) -> pd.Series:
    """
    Bygger ett target från ett dataset.

    Classification:
        Returnerar 0/1 beroende på om return-värdet
        passerar targetens threshold.

    Regression:
        Returnerar den observerade target-kolumnen
        utan klassificering.
    """

    if target.task == "regression":
        if not target.target_column:
            raise ValueError(
                "Regression-target saknar "
                f"target_column: {target.id}"
            )

        if target.target_column not in frame.columns:
            raise ValueError(
                "Saknar target-kolumn: "
                f"{target.target_column}"
            )

        return pd.to_numeric(
            frame[target.target_column],
            errors="coerce",
        ).astype(float)

    if target.return_column not in frame.columns:
        raise ValueError(
            "Saknar return-kolumn: "
            f"{target.return_column}"
        )

    values = pd.to_numeric(
        frame[target.return_column],
        errors="coerce",
    )

    result = pd.Series(
        np.nan,
        index=frame.index,
        dtype=float,
    )

    valid = values.notna()

    if target.direction == "above":
        result.loc[valid] = (
            values.loc[valid]
            > target.threshold
        ).astype(float)

    elif target.direction == "below":
        result.loc[valid] = (
            values.loc[valid]
            <= target.threshold
        ).astype(float)

    else:
        raise ValueError(
            "Okänd target-riktning: "
            f"{target.direction}"
        )

    return result
