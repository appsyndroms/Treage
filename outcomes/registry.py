"""Register för Treuddens research targets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent
    / "target_registry.json"
)


@dataclass(frozen=True)
class TargetDefinition:
    """Definition av ett target i Treuddens target-register."""

    id: str
    return_column: str
    threshold: float = 0.0
    direction: str = "above"
    task: str = "classification"
    target_column: str | None = None


class TargetRegistry:
    """Läser och tillhandahåller target-definitioner."""

    def __init__(
        self,
        path: Path | str = DEFAULT_REGISTRY_PATH,
    ) -> None:
        self.path = Path(path)
        self._targets = self._load()

    def _load(self) -> dict[str, TargetDefinition]:
        with self.path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        targets: dict[str, TargetDefinition] = {}

        for item in data.get("targets", []):
            definition = TargetDefinition(
                id=item["id"],
                return_column=item["return_column"],
                threshold=float(
                    item.get("threshold", 0.0)
                ),
                direction=item.get(
                    "direction",
                    "above",
                ),
                task=item.get(
                    "task",
                    "classification",
                ),
                target_column=item.get(
                    "target_column"
                ),
            )

            if definition.id in targets:
                raise ValueError(
                    "Dubblett i target-registret: "
                    f"{definition.id}"
                )

            targets[definition.id] = definition

        return targets

    def get(
        self,
        target_id: str,
    ) -> TargetDefinition:
        """Hämtar en target-definition."""
        try:
            return self._targets[target_id]
        except KeyError as exc:
            raise ValueError(
                f"Okänt target: {target_id}"
            ) from exc

    def all(self) -> list[TargetDefinition]:
        """Returnerar alla registrerade targets."""
        return list(self._targets.values())

    def by_task(
        self,
        task: str,
    ) -> list[TargetDefinition]:
        """Returnerar targets för en viss task-typ."""
        return [
            target
            for target in self._targets.values()
            if target.task == task
        ]

    def validate_frame(
        self,
        frame: pd.DataFrame,
        target_id: str,
    ) -> None:
        """Kontrollerar att targetens nödvändiga kolumn finns."""

        definition = self.get(target_id)

        required_column = (
            definition.target_column
            if definition.task == "regression"
            and definition.target_column
            else definition.return_column
        )

        if required_column not in frame.columns:
            raise ValueError(
                f"Target '{target_id}' kräver kolumn "
                f"'{required_column}'."
            )


def load_target_registry(
    path: Path | str = DEFAULT_REGISTRY_PATH,
) -> TargetRegistry:
    """Skapar ett target-register från JSON."""
    return TargetRegistry(path)
