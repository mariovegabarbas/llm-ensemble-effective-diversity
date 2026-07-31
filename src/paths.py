"""Repository paths.

Every path used by the analysis is derived from the repository root, which is
located relative to this file. Nothing here depends on where the repository is
checked out. Set the environment variable ``CDI_DATA_ROOT`` to point the scripts
at data held outside the working tree.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA = Path(os.environ.get("CDI_DATA_ROOT", ROOT / "data"))
INDICES = DATA / "indices"
FORMULATIONS = DATA / "formulations"

RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
DOCS = ROOT / "docs"

ENSEMBLE_INDICES = INDICES / "ensemble_indices.csv"
PER_MODEL_DISSENT = INDICES / "per_model_dissent.csv"
RUN_EXCLUSIONS = INDICES / "run_exclusions.json"
VIGNETTE_STRATA = INDICES / "vignette_strata.csv"
FORMULATIONS_JSONL = FORMULATIONS / "formulations.jsonl"


def ensure_results() -> Path:
    """Create the results directory on first use and return it."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    return RESULTS
