from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent
    / "research_registry.json"
)


@dataclass(frozen=True)
class ResearchRegistry:
    modes: frozenset[str]
    analysis_types: frozenset[str]
    directions: frozenset[str]
    analysis_signal_requirements: dict[
        str,
        tuple[int, int | None],
    ]
    analysis_rules: dict[
        str,
        dict[str, Any],
    ]


def load_research_registry(
    path: str | Path = DEFAULT_REGISTRY_PATH,
) -> ResearchRegistry:
    """Läser research-registret från JSON."""

    registry_path = Path(path)

    with registry_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        payload = json.load(handle)

    requirements: dict[
        str,
        tuple[int, int | None],
    ] = {}

    for analysis_type, value in payload.get(
        "analysis_signal_requirements",
        {},
    ).items():
        minimum = int(
            value["min"]
        )

        maximum = value.get(
            "max"
        )

        requirements[
            str(analysis_type)
        ] = (
            minimum,
            None
            if maximum is None
            else int(maximum),
        )

    raw_rules = payload.get(
        "analysis_rules",
        {},
    )

    if not isinstance(raw_rules, dict):
        raise ValueError(
            "analysis_rules måste vara ett objekt."
        )

    analysis_rules = {
        str(analysis_type): dict(rules)
        for analysis_type, rules in raw_rules.items()
        if isinstance(rules, dict)
    }

    return ResearchRegistry(
        modes=frozenset(
            str(value)
            for value in payload.get(
                "modes",
                [],
            )
        ),
        analysis_types=frozenset(
            str(value)
            for value in payload.get(
                "analysis_types",
                [],
            )
        ),
        directions=frozenset(
            str(value)
            for value in payload.get(
                "directions",
                [],
            )
        ),
        analysis_signal_requirements=requirements,
        analysis_rules=analysis_rules,
    )


@dataclass(frozen=True)
class SignalSpec:
    name: str
    direction: str = "upper"
    bins: tuple[float, ...] = (0.10,)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(
                "Signal måste ha ett namn."
            )

        if not self.bins:
            raise ValueError(
                "Signal måste ha minst en bin."
            )

        for fraction in self.bins:
            if not 0 < fraction <= 1:
                raise ValueError(
                    f"Ogiltig signal bin: "
                    f"{fraction}"
                )


@dataclass(frozen=True)
class AnalysisSpec:
    type: str = "tail"
    bootstrap: bool = False
    bootstrap_iterations: int = 2000
    rules: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.bootstrap_iterations < 1:
            raise ValueError(
                "bootstrap_iterations måste vara > 0."
            )


@dataclass(frozen=True)
class ResearchSpec:
    id: str
    question: str
    signals: tuple[SignalSpec, ...]
    targets: tuple[str, ...]
    analysis: AnalysisSpec = field(
        default_factory=AnalysisSpec
    )
    mode: str = "scan"
    windows: tuple[str, ...] = (
        "window_1",
        "window_2",
    )
    splits: tuple[str, ...] = (
        "test",
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError(
                "Research spec saknar id."
            )

        if not self.question:
            raise ValueError(
                "Research spec saknar question."
            )

        if not self.signals:
            raise ValueError(
                "Research spec måste ha minst "
                "en signal."
            )

        if not self.targets:
            raise ValueError(
                "Research spec måste ha minst "
                "ett target."
            )

        if not self.windows:
            raise ValueError(
                "Research spec måste ha minst "
                "ett window."
            )

        if not self.splits:
            raise ValueError(
                "Research spec måste ha minst "
                "ett split."
            )


def _tuple_floats(
    values: Any,
) -> tuple[float, ...]:
    if values is None:
        return ()

    return tuple(
        float(value)
        for value in values
    )


def _validate_signal(
    signal: SignalSpec,
    registry: ResearchRegistry,
) -> None:
    if signal.direction not in registry.directions:
        raise ValueError(
            f"Ogiltig signal direction: "
            f"{signal.direction}"
        )


def _validate_analysis(
    analysis: AnalysisSpec,
    signals: tuple[SignalSpec, ...],
    registry: ResearchRegistry,
) -> None:
    if analysis.type not in registry.analysis_types:
        raise ValueError(
            f"Ogiltig analysis.type: "
            f"{analysis.type}"
        )

    requirement = (
        registry.analysis_signal_requirements.get(
            analysis.type
        )
    )

    if requirement is None:
        raise ValueError(
            f"Analysform saknar signal-krav i "
            f"research-registret: "
            f"{analysis.type}"
        )

    min_signals, max_signals = requirement
    signal_count = len(signals)

    if signal_count < min_signals:
        if max_signals == min_signals:
            raise ValueError(
                f"{analysis.type} kräver "
                f"exakt {min_signals} signaler."
            )

        raise ValueError(
            f"{analysis.type} kräver "
            f"minst {min_signals} signaler."
        )

    if (
        max_signals is not None
        and signal_count > max_signals
    ):
        raise ValueError(
            f"{analysis.type} kräver "
            f"exakt {max_signals} signaler."
        )

    rules = registry.analysis_rules.get(
        analysis.type
    )

    if rules is None:
        return

    stratification_signals = rules.get(
        "stratification_signals"
    )

    test_signal = rules.get(
        "test_signal"
    )

    if stratification_signals is not None:
        stratification_signals = int(
            stratification_signals
        )

        if (
            stratification_signals < 1
            or stratification_signals >= signal_count
        ):
            raise ValueError(
                f"{analysis.type} har ogiltigt antal "
                f"stratification_signals: "
                f"{stratification_signals}"
            )

    if test_signal is not None:
        test_signal = int(
            test_signal
        )

        if (
            test_signal < 1
            or test_signal > signal_count
        ):
            raise ValueError(
                f"{analysis.type} har ogiltigt "
                f"test_signal: {test_signal}"
            )

    minimum_bins = rules.get(
        "minimum_bins_per_stratification_signal"
    )

    if minimum_bins is not None:
        minimum_bins = int(
            minimum_bins
        )

        if minimum_bins < 1:
            raise ValueError(
                f"{analysis.type} har ogiltigt "
                f"minimum_bins_per_stratification_signal: "
                f"{minimum_bins}"
            )

        if stratification_signals is None:
            raise ValueError(
                f"{analysis.type} anger minimum bins "
                f"utan stratification_signals."
            )

        for index in range(
            stratification_signals
        ):
            signal = signals[index]

            if len(signal.bins) < minimum_bins:
                raise ValueError(
                    f"{analysis.type} kräver minst "
                    f"{minimum_bins} bins för "
                    f"stratifieringssignal "
                    f"{index + 1}: "
                    f"{signal.name}"
                )


def validate_spec(
    spec: ResearchSpec,
    registry: ResearchRegistry | None = None,
) -> None:
    """Validerar en färdig ResearchSpec mot research-registret."""

    if registry is None:
        registry = load_research_registry()

    if spec.mode not in registry.modes:
        raise ValueError(
            f"Ogiltigt research mode: "
            f"{spec.mode}"
        )

    for signal in spec.signals:
        _validate_signal(
            signal,
            registry,
        )

    _validate_analysis(
        analysis=spec.analysis,
        signals=spec.signals,
        registry=registry,
    )


def load_spec(
    path: str | Path,
    registry: ResearchRegistry | None = None,
) -> ResearchSpec:
    """Läser och validerar en YAML-baserad research-spec."""

    if registry is None:
        registry = load_research_registry()

    path = Path(path)

    payload = yaml.safe_load(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, dict):
        raise ValueError(
            f"Research spec måste vara ett objekt: {path}"
        )

    spec_id = payload.get("id")
    question = payload.get("question")

    if not spec_id:
        raise ValueError(
            f"Research spec saknar id: {path}"
        )

    if not question:
        raise ValueError(
            f"Research spec saknar question: {path}"
        )

    mode = str(
        payload.get(
            "mode",
            "scan",
        )
    ).lower()

    if mode not in registry.modes:
        raise ValueError(
            f"Ogiltigt mode '{mode}' i {path}"
        )

    raw_signals = payload.get(
        "signals",
        [],
    )

    if not raw_signals:
        raise ValueError(
            f"Research spec saknar signals: {path}"
        )

    signals: list[SignalSpec] = []

    for item in raw_signals:
        if not isinstance(item, dict):
            raise ValueError(
                f"Ogiltig signaldefinition i {path}"
            )

        name = item.get("name")

        if not name:
            raise ValueError(
                f"Signal saknar name i {path}"
            )

        direction = str(
            item.get(
                "direction",
                "upper",
            )
        ).lower()

        bins = _tuple_floats(
            item.get(
                "bins",
                (0.10,),
            )
        )

        signal = SignalSpec(
            name=str(name),
            direction=direction,
            bins=bins,
        )

        _validate_signal(
            signal,
            registry,
        )

        signals.append(
            signal
        )

    targets = tuple(
        str(target)
        for target in payload.get(
            "targets",
            [],
        )
    )

    if not targets:
        raise ValueError(
            f"Research spec saknar targets: {path}"
        )

    raw_analysis = payload.get(
        "analysis",
        {},
    )

    if not isinstance(raw_analysis, dict):
        raise ValueError(
            f"analysis måste vara ett objekt: {path}"
        )

    analysis_type = str(
        raw_analysis.get(
            "type",
            "tail",
        )
    ).lower()

    bootstrap = bool(
        raw_analysis.get(
            "bootstrap",
            False,
        )
    )

    bootstrap_iterations = int(
        raw_analysis.get(
            "bootstrap_iterations",
            2000,
        )
    )

    analysis_rules = dict(
        registry.analysis_rules.get(
            analysis_type,
            {},
        )
    )

    analysis = AnalysisSpec(
        type=analysis_type,
        bootstrap=bootstrap,
        bootstrap_iterations=(
            bootstrap_iterations
        ),
        rules=analysis_rules,
    )

    _validate_analysis(
        analysis=analysis,
        signals=tuple(signals),
        registry=registry,
    )

    windows = tuple(
        str(window)
        for window in payload.get(
            "windows",
            (
                "window_1",
                "window_2",
            ),
        )
    )

    if not windows:
        raise ValueError(
            "Research spec måste ha minst ett window."
        )

    splits = tuple(
        str(split)
        for split in payload.get(
            "splits",
            ("test",),
        )
    )

    if not splits:
        raise ValueError(
            "Research spec måste ha minst ett split."
        )

    metadata = payload.get(
        "metadata",
        {},
    )

    if not isinstance(metadata, dict):
        raise ValueError(
            f"metadata måste vara ett objekt: {path}"
        )

    spec = ResearchSpec(
        id=str(spec_id),
        question=str(question),
        signals=tuple(signals),
        targets=targets,
        analysis=analysis,
        mode=mode,
        windows=windows,
        splits=splits,
        metadata=dict(metadata),
    )

    validate_spec(
        spec,
        registry,
    )

    return spec
