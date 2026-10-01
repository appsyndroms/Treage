from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from features.registry import SignalRegistry
from outcomes.registry import TargetRegistry
from research.cache import (
    ResearchCache,
    ResearchRequirement,
    build_research_cache,
)


@dataclass
class ResearchSession:
    """
    Gemensam context för en hel research-körning.

    Alla specs som körs tillsammans delar samma DataFrame
    och samma ResearchCache.
    """

    frame: pd.DataFrame
    cache: ResearchCache


def _required_requirements(
    specs,
) -> list[ResearchRequirement]:
    requirements: list[ResearchRequirement] = []

    seen: set[tuple] = set()

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
    specs,
    frame_loader: Callable[[], pd.DataFrame],
    signal_registry: SignalRegistry,
    target_registry: TargetRegistry,
    windows,
) -> ResearchSession:
    """
    Bygger en gemensam research-session.

    Data laddas av den caller som känner till datakällan.
    Research-lagret behöver därför inte känna till om datan
    kommer från blankning, insiderdata, rapporter eller en
    kombination av dessa.
    """
    print(
        "Loading research data...",
        flush=True,
    )

    frame = frame_loader()

    print(
        f"Loaded {len(frame):,} research rows",
        flush=True,
    )

    requirements = _required_requirements(
        specs
    )

    print(
        "Cache requirements: "
        f"{len(requirements):,}",
        flush=True,
    )

    print(
        "Building shared research cache...",
        flush=True,
    )

    cache = build_research_cache(
        frame=frame,
        requirements=requirements,
        target_registry=target_registry,
        signal_registry=signal_registry,
        windows=windows,
    )

    print(
        "Shared research cache ready.",
        flush=True,
    )

    return ResearchSession(
        frame=frame,
        cache=cache,
    )
