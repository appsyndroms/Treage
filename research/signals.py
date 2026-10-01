"""Generiska signaloperationer för Treudden research."""

from __future__ import annotations

import numpy as np
import pandas as pd


def require_column(
    frame: pd.DataFrame,
    column: str,
) -> None:
    """Kontrollerar att en feature-kolumn finns."""
    if column not in frame.columns:
        raise ValueError(
            f"Saknar feature-kolumn '{column}'."
        )


def numeric_signal(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    """
    Hämtar en numerisk signal från ett feature-dataset.

    Funktionen känner inte till signalens källa eller betydelse.
    Signalen kan exempelvis komma från blankning, insiderdata,
    rapporter, marknad eller sektor.
    """
    require_column(frame, column)

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    ).replace(
        [np.inf, -np.inf],
        np.nan,
    )


def tail_mask(
    frame: pd.DataFrame,
    signal: pd.Series,
    fraction: float,
    direction: str = "upper",
) -> pd.Series:
    """
    Väljer tvärsnittets övre eller undre tail per snapshot_date.

    Exempel:
        fraction=0.05, direction="upper"
        -> högsta 5 % varje snapshot-datum.

        fraction=0.05, direction="lower"
        -> lägsta 5 % varje snapshot-datum.

    Rangordningen görs inom varje snapshot-datum så att
    signalnivåer mellan olika perioder inte blandas ihop.
    """
    if not 0 < fraction <= 1:
        raise ValueError(
            f"Ogiltig tail-fraktion: {fraction}"
        )

    if direction not in {"upper", "lower"}:
        raise ValueError(
            f"Ogiltig tail-riktning: {direction}"
        )

    if "snapshot_date" not in frame.columns:
        raise ValueError(
            "Saknar kolumn 'snapshot_date'."
        )

    working = pd.DataFrame(
        {
            "snapshot_date": frame["snapshot_date"],
            "signal": signal,
        },
        index=frame.index,
    )

    valid = working["signal"].notna()

    rank = pd.Series(
        np.nan,
        index=frame.index,
        dtype=float,
    )

    rank.loc[valid] = (
        working.loc[valid]
        .groupby("snapshot_date")["signal"]
        .rank(
            pct=True,
            method="average",
        )
    )

    if direction == "upper":
        return rank >= (1.0 - fraction)

    return rank <= fraction
