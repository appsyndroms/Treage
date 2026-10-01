from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from .registry import SignalRegistry


@dataclass(frozen=True)
class FeatureDataset:
    """
    Dataunderlaget som används av Treuddens research-lager.

    FeatureDataset känner inte till research, targets eller
    analysmetoder. Det representerar endast ett feature-frame
    tillsammans med dess signalregister.
    """

    frame: pd.DataFrame
    registry: SignalRegistry

    def validate(self) -> None:
        """Validerar att datasetet innehåller registrerade signaler."""
        for signal in self.registry.all():
            self.registry.validate_frame(
                self.frame,
                signal.id,
            )

    def signal_column(
        self,
        signal_name: str,
    ) -> pd.Series:
        """Returnerar kolumnen som hör till en registrerad signal."""
        definition = self.registry.get(
            signal_name
        )

        self.registry.validate_frame(
            self.frame,
            signal_name,
        )

        return self.frame[
            definition.column
        ]


def load_features(
    loader: Callable[[], pd.DataFrame],
    registry: SignalRegistry,
) -> FeatureDataset:
    """
    Laddar ett feature-dataset via ett externt loader-interface.

    Research-lagret behöver inte känna till om data kommer från
    JSONL, parquet, databas, API eller någon annan källa.
    """

    frame = loader()

    if not isinstance(frame, pd.DataFrame):
        raise TypeError(
            "Feature loader must return a pandas DataFrame."
        )

    dataset = FeatureDataset(
        frame=frame,
        registry=registry,
    )

    return dataset
