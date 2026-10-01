"""Register för Treuddens forskningssignaler."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent / "signal_registry.json"
)


@dataclass(frozen=True)
class SignalDefinition:
    """Definition av en signal i Treuddens signalregister."""

    id: str
    source: str
    column: str
    type: str
    description: str


class SignalRegistry:
    """Läser och tillhandahåller signaldefinitioner."""

    def __init__(
        self,
        path: Path | str = DEFAULT_REGISTRY_PATH,
    ) -> None:
        self.path = Path(path)
        self._signals = self._load()

    def _load(self) -> dict[str, SignalDefinition]:
        with self.path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        signals: dict[str, SignalDefinition] = {}

        for item in data.get("signals", []):
            definition = SignalDefinition(
                id=item["id"],
                source=item["source"],
                column=item["column"],
                type=item["type"],
                description=item.get("description", ""),
            )

            if definition.id in signals:
                raise ValueError(
                    f"Dubblett i signalregistret: {definition.id}"
                )

            signals[definition.id] = definition

        return signals

    def get(
        self,
        signal_id: str,
    ) -> SignalDefinition:
        """Hämtar en signaldefinition."""
        try:
            return self._signals[signal_id]
        except KeyError as exc:
            raise ValueError(
                f"Okänd signal: {signal_id}"
            ) from exc

    def all(self) -> list[SignalDefinition]:
        """Returnerar alla registrerade signaler."""
        return list(self._signals.values())

    def by_source(
        self,
        source: str,
    ) -> list[SignalDefinition]:
        """Returnerar alla signaler från en viss källa."""
        return [
            signal
            for signal in self._signals.values()
            if signal.source == source
        ]

    def column_for(
        self,
        signal_id: str,
    ) -> str:
        """Returnerar feature-kolumnen för en signal."""
        return self.get(signal_id).column

    def validate_frame(
        self,
        frame: pd.DataFrame,
        signal_id: str,
    ) -> None:
        """Kontrollerar att signalens feature finns i datasetet."""
        definition = self.get(signal_id)

        if definition.column not in frame.columns:
            raise ValueError(
                f"Signal '{signal_id}' kräver kolumn "
                f"'{definition.column}'."
            )


def load_signal_registry(
    path: Path | str = DEFAULT_REGISTRY_PATH,
) -> SignalRegistry:
    """Skapar ett signalregister från JSON."""
    return SignalRegistry(path)
