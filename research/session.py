from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..features.dataset import FeatureDataset
from ..outcomes.registry import TargetRegistry
from .cache import (
    ResearchCache,
    ResearchRequirement,
    build_research_cache,
)
from .spec import ResearchSpec


@dataclass
class ResearchSession:
    dataset: FeatureDataset
    cache: ResearchCache


def _required_requirements(
    specs: Sequence[ResearchSpec],
) -> list[ResearchRequirement]:
    """
    Bygger en unik lista över allt som research-sessionen behöver
    för att kunna köra de angivna specifikationerna.
    """

    requirements: list[
        ResearchRequirement
    ] = []

    seen: set[
        tuple[
            str,
            str,
            float,
            str,
        ]
    ] = set()

    for spec in specs:
        for signal in spec.signals:
            for target_name in spec.targets:
                for fraction in signal.bins:
                    key = (
                        signal.name,
                        target_name,
                        fraction,
                        signal.direction,
                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    requirements.append(
                        ResearchRequirement(
                            signal_name=signal.name,
                            target_name=target_name,
                            tail_fraction=fraction,
                            tail_direction=signal.direction,
                        )
                    )

    return requirements


def build_session(
    specs: Sequence[ResearchSpec],
    dataset: FeatureDataset,
    target_registry: TargetRegistry,
    windows,
) -> ResearchSession:
    """
    Bygger en research-session från ett färdigt FeatureDataset.

    Research-lagret behöver därmed inte känna till om datat kommer
    från JSONL, parquet, databas, API eller någon annan källa.
    """

    dataset.validate()

    requirements = _required_requirements(
        specs
    )

    cache = build_research_cache(
        dataset=dataset,
        requirements=requirements,
        target_registry=target_registry,
        windows=windows,
    )

    return ResearchSession(
        dataset=dataset,
        cache=cache,
    )
