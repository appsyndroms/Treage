"""Gemensam signalhantering för Treuddens research."""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.registry import (
    SignalRegistry,
)


def build_signal(
    frame: pd.DataFrame,
    signal_name: str,
    registry: SignalRegistry,
) -> pd.Series:
    """
    Returnerar en numerisk signal.

    Signalens definition hämtas från SignalRegistry.
    Research-lagret behöver därför inte känna till
    vilken datakälla eller feature-kolumn signalen använder.
    """
    definition = registry.get(
        signal_name
    )

    registry.validate_frame(
        frame,
        signal_name,
    )

    return pd.to_numeric(
        frame[definition.column],
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

    Rangordningen görs per snapshot-datum så att ett experiment
    inte domineras av perioder med generellt högre eller lägre
    signalnivåer.
    """
    if not 0 < fraction <= 1:
        raise ValueError(
            f"Ogiltig tail-fraktion: {fraction}"
        )

    if direction not in {
        "upper",
        "lower",
    }:
        raise ValueError(
            f"Ogiltig tail-riktning: {direction}"
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


def signal_direction(
    signal_name: str,
    registry: SignalRegistry,
) -> str:
    """
    Returnerar signalens standardriktning.

    Riktningen ska i första hand beskrivas av signalens
    metadata i registret, inte av hårdkodade signalnamn.
    """
    definition = registry.get(
        signal_name
    )

    direction = getattr(
        definition,
        "direction",
        None,
    )

    if direction is None:
        raise ValueError(
            "Signal saknar standardriktning: "
            f"{signal_name}"
        )

    return direction


def all_signal_names(
    registry: SignalRegistry,
) -> list[str]:
    """Returnerar alla registrerade signal-ID:n."""
    return [
        signal.id
        for signal in registry.all()
    ]
