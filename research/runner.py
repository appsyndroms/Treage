from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from ..features.dataset import FeatureDataset
from ..features.registry import load_signal_registry
from ..outcomes.registry import load_target_registry
from .engine import run_spec
from .session import build_session
from .spec import (
    ResearchSpec,
    load_research_registry,
    load_spec,
)

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SPEC_DIR = (
    ROOT
    / "research"
    / "specs"
)


def _find_specs(
    spec_dir: Path,
) -> list[Path]:
    return sorted(
        spec_dir.glob("*.yaml")
    )


def _validate_unique_spec_ids(
    specs: Sequence[ResearchSpec],
    spec_paths: Sequence[Path],
) -> None:
    seen: dict[str, Path] = {}

    for spec, path in zip(
        specs,
        spec_paths,
    ):
        previous = seen.get(
            spec.id
        )

        if previous is not None:
            raise ValueError(
                "Duplicate research spec id "
                f"'{spec.id}'.\n"
                f"First: {previous}\n"
                f"Duplicate: {path}"
            )

        seen[spec.id] = path


def _validate_mode(
    specs: Sequence[ResearchSpec],
    spec_paths: Sequence[Path],
    mode: str | None,
) -> None:
    if mode is None:
        return

    invalid = [
        (spec, path)
        for spec, path in zip(
            specs,
            spec_paths,
        )
        if spec.mode != mode
    ]

    if not invalid:
        return

    details = "\n".join(
        (
            f"- {path}: "
            f"spec mode='{spec.mode}', "
            f"requested='{mode}'"
        )
        for spec, path in invalid
    )

    raise ValueError(
        "Research spec har fel mode för "
        f"'{mode}':\n{details}"
    )


def _load_specs(
    spec_paths: Sequence[Path],
    *,
    mode: str | None,
    filter_mode: bool,
    registry,
) -> tuple[
    list[ResearchSpec],
    list[Path],
]:
    if not spec_paths:
        raise ValueError(
            "Hittade inga research specs."
        )

    loaded_specs = [
        load_spec(
            path,
            registry=registry,
        )
        for path in spec_paths
    ]

    _validate_unique_spec_ids(
        loaded_specs,
        spec_paths,
    )

    if filter_mode and mode is not None:
        selected = [
            (spec, path)
            for spec, path in zip(
                loaded_specs,
                spec_paths,
            )
            if spec.mode == mode
        ]

        if not selected:
            raise ValueError(
                "Hittade inga research specs "
                f"med mode='{mode}'."
            )

        return (
            [spec for spec, _ in selected],
            [path for _, path in selected],
        )

    _validate_mode(
        loaded_specs,
        spec_paths,
        mode,
    )

    return (
        loaded_specs,
        list(spec_paths),
    )


def run_research(
    dataset: FeatureDataset,
    windows,
    spec_paths: Sequence[str | Path] | None = None,
    *,
    mode: str | None = None,
) -> dict:
    """
    Kör declarativ research från YAML-specifikationer.

    Runnern ansvarar för orkestrering men innehåller ingen
    research-specifik signal-, target-, analys- eller
    walk-forward-konfiguration.
    """

    research_registry = (
        load_research_registry()
    )

    if mode is not None:
        mode = str(mode).lower()

        if mode not in research_registry.modes:
            raise ValueError(
                f"Ogiltigt research mode: {mode}"
            )

    explicit_specs = bool(
        spec_paths
    )

    if explicit_specs:
        resolved_spec_paths = [
            Path(path)
            for path in spec_paths
        ]
    else:
        resolved_spec_paths = _find_specs(
            DEFAULT_SPEC_DIR
        )

    specs, selected_spec_paths = _load_specs(
        resolved_spec_paths,
        mode=mode,
        filter_mode=not explicit_specs,
        registry=research_registry,
    )

    signal_registry = (
        load_signal_registry()
    )

    target_registry = (
        load_target_registry()
    )

    session = build_session(
        specs=specs,
        dataset=dataset,
        signal_registry=signal_registry,
        target_registry=target_registry,
        windows=windows,
    )

    results = []

    for spec, spec_path in zip(
        specs,
        selected_spec_paths,
    ):
        result = run_spec(
            session.cache,
            spec,
        )

        results.append(
            {
                "spec": spec,
                "spec_path": spec_path,
                "result": result,
            }
        )

    return {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "mode": mode,
        "results": results,
    }


def main() -> None:
    raise SystemExit(
        "CLI-entrypoint implementeras när "
        "Treuddens datakällor och runtime-"
        "konfiguration är kopplade."
    )


if __name__ == "__main__":
    main()
