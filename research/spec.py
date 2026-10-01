"""Specifikationer och validering för Treuddens research."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent / "research_registry.json"
)


@dataclass(frozen=True)
class SignalSpec:
    name: str
    direction: str
    bins: tuple[float, ...]


@dataclass(frozen=True)
class AnalysisSpec:
    type: str
    params: dict[str, Any]


@dataclass(frozen=True)
class ResearchSpec:
    id: str
    question: str
    mode: str
    signals: tuple[SignalSpec, ...]
    targets: tuple[str, ...]
    analysis: AnalysisSpec
    derived_metrics: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisSignalRequirement:
    minimum: int
    maximum: int | None


@dataclass(frozen=True)
class ResearchRegistry:
    modes: frozenset[str]
    analysis_types: frozenset[str]
    directions: frozenset[str]
    signal_requirements: dict[
        str,
        AnalysisSignalRequirement,
    ]


def load_research_registry(
    path: Path | str = DEFAULT_REGISTRY_PATH,
) -> ResearchRegistry:
    """Läser research-registret från JSON."""

    registry_path = Path(path)

    with registry_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        data = json.load(handle)

    requirements = {}

    for analysis_type, requirement in data.get(
        "analysis_signal_requirements",
        {},
    ).items():
        requirements[analysis_type] = AnalysisSignalRequirement(
            minimum=int(requirement["min"]),
            maximum=(
                None
                if requirement.get("max") is None
                else int(requirement["max"])
            ),
        )

    return ResearchRegistry(
        modes=frozenset(
            data.get("modes", [])
        ),
        analysis_types=frozenset(
            data.get("analysis_types", [])
        ),
        directions=frozenset(
            data.get("directions", [])
        ),
        signal_requirements=requirements,
    )


def _validate_signal_spec(
    signal: SignalSpec,
    registry: ResearchRegistry,
) -> None:
    if signal.direction not in registry.directions:
        raise ValueError(
            f"Ogiltig signalriktning: {signal.direction}"
        )

    if not signal.bins:
        raise ValueError(
            f"Signal saknar bins: {signal.name}"
        )

    for fraction in signal.bins:
        if not 0 < fraction <= 1:
            raise ValueError(
                f"Ogiltig bin-fraktion för "
                f"{signal.name}: {fraction}"
            )


def _validate_analysis(
    analysis: AnalysisSpec,
    signal_count: int,
    registry: ResearchRegistry,
) -> None:
    if analysis.type not in registry.analysis_types:
        raise ValueError(
            f"Okänd analysform: {analysis.type}"
        )

    requirement = registry.signal_requirements.get(
        analysis.type
    )

    if requirement is None:
        raise ValueError(
            f"Analysform saknar signal-krav i "
            f"research-registret: {analysis.type}"
        )

    if signal_count < requirement.minimum:
        raise ValueError(
            f"Analysen '{analysis.type}' kräver minst "
            f"{requirement.minimum} signaler, "
            f"men fick {signal_count}."
        )

    if (
        requirement.maximum is not None
        and signal_count > requirement.maximum
    ):
        raise ValueError(
            f"Analysen '{analysis.type}' tillåter högst "
            f"{requirement.maximum} signaler, "
            f"men fick {signal_count}."
        )


def validate_spec(
    spec: ResearchSpec,
    registry: ResearchRegistry | None = None,
) -> None:
    """Validerar en research-specifikation."""

    if registry is None:
        registry = load_research_registry()

    if not spec.id:
        raise ValueError(
            "Research-spec saknar id."
        )

    if not spec.question:
        raise ValueError(
            f"Research-spec '{spec.id}' saknar question."
        )

    if spec.mode not in registry.modes:
        raise ValueError(
            f"Ogiltigt research-mode: {spec.mode}"
        )

    if not spec.signals:
        raise ValueError(
            f"Research-spec '{spec.id}' saknar signaler."
        )

    if not spec.targets:
        raise ValueError(
            f"Research-spec '{spec.id}' saknar targets."
        )

    for signal in spec.signals:
        _validate_signal_spec(
            signal,
            registry,
        )

    _validate_analysis(
        analysis=spec.analysis,
        signal_count=len(spec.signals),
        registry=registry,
    )


def build_spec(
    data: dict[str, Any],
    registry: ResearchRegistry | None = None,
) -> ResearchSpec:
    """Bygger och validerar en ResearchSpec från en dict."""

    if registry is None:
        registry = load_research_registry()

    signals = tuple(
        SignalSpec(
            name=item["name"],
            direction=item["direction"],
            bins=tuple(
                float(value)
                for value in item["bins"]
            ),
        )
        for item in data.get("signals", [])
    )

    analysis_data = data.get(
        "analysis",
        {},
    )

    analysis = AnalysisSpec(
        type=analysis_data["type"],
        params=dict(
            analysis_data.get(
                "params",
                {},
            )
        ),
    )

    spec = ResearchSpec(
        id=data["id"],
        question=data["question"],
        mode=data["mode"],
        signals=signals,
        targets=tuple(
            data.get("targets", [])
        ),
        analysis=analysis,
        derived_metrics=tuple(
            data.get(
                "derived_metrics",
                [],
            )
        ),
    )

    validate_spec(
        spec,
        registry,
    )

    return spec
