"""Build the published data files from the study's internal artifacts.

This script is the boundary between the internal run directory and the published
repository: it renames every field to its English published name and writes the
files under ``data/``. It is kept in the repository so the published data can be
audited against the artifacts they come from, but it is **not** part of the
reproduction path: a user of this repository consumes ``data/`` directly.

    python3 src/export_data.py --run-dir PATH_TO_INTERNAL_RUN

``docs/field_mapping.md`` records the full correspondence between published and
internal field names, so the numbers in the manuscript remain reconcilable with
the ones here.
"""
import argparse
import csv
import json
from pathlib import Path

import paths

# published name <- internal name
ENSEMBLE_FIELDS = {
    "vignette_id": "vineta_id",
    "run_id": "run_id",
    "s_norm": "S_norm",
    "n_eff": "N_eff",
    "condition_number": "cond",
    "n_voices": "n_voces",
}
DISSENT_FIELDS = {
    "vignette_id": "vineta_id",
    "run_id": "run_id",
    "model": "model",
    "d_i": "d_i",
    "n_voices_in_run": "n_voces_corrida",
}
# Design labels are translated; the framework labels are not, because they are
# data: the models were shown a Spanish menu and their replies quote it.
CLINICAL_PICTURE = {
    "depresion": "depression",
    "trauma": "trauma",
    "abuso_de_sustancias": "substance_abuse",
    "conflicto_vincular": "relational_conflict",
}
OPENNESS_STRATUM = {
    "marco_compartido_ineficaz": "shared_frame_ineffective",
    "marco_compartido_effective": "shared_frame_effective",
    "marco_compartido_eficaz": "shared_frame_effective",
    "marco_genuinamente_distinto": "genuinely_distinct",
}


def export_indices(run_dir: Path, clean: Path) -> None:
    paths.INDICES.mkdir(parents=True, exist_ok=True)

    for source, fields, destination in (
        (clean / "exploratory_ensemble_indices.csv", ENSEMBLE_FIELDS, paths.ENSEMBLE_INDICES),
        (clean / "confirmatory_per_model_dissent.csv", DISSENT_FIELDS, paths.PER_MODEL_DISSENT),
    ):
        rows = list(csv.DictReader(source.open()))
        with destination.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fields))
            writer.writeheader()
            for row in rows:
                writer.writerow({new: row[old] for new, old in fields.items()})
        print(f"  {destination.name}: {len(rows)} rows")

    exclusions = json.loads((clean / "per_run_exclusions.json").read_text())
    published = {}
    for key, value in exclusions.items():
        vignette, run = key.split("/")
        published[f"{vignette}/{int(run.split('_')[1])}"] = {
            "n_valid": value["n_valid"],
            "n_present": value["n_present"],
            "absent": value["absent"],
            "degenerate": value["degenerate"],
        }
    paths.RUN_EXCLUSIONS.write_text(json.dumps(published, indent=1, sort_keys=True))
    print(f"  {paths.RUN_EXCLUSIONS.name}: {len(published)} runs")


def export_strata(bank_path: Path) -> None:
    """Design labels of each vignette, without any vignette text.

    The vignette bank itself is not published; these two design columns are, so
    that the stratified analyses can be reproduced without the clinical material.
    """
    bank = json.loads(bank_path.read_text())
    with paths.VIGNETTE_STRATA.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["vignette_id", "clinical_picture", "openness_stratum"])
        for case in bank["casos"]:
            grid = case["grilla_primaria"]
            writer.writerow([
                case["case_id"],
                CLINICAL_PICTURE[grid["cuadro"]],
                OPENNESS_STRATUM[grid["apertura_interpretativa"]],
            ])
    print(f"  {paths.VIGNETTE_STRATA.name}: {len(bank['casos'])} vignettes")


def export_formulations(run_dir: Path, clean: Path) -> None:
    """One JSON object per formulation, in a single JSONL file.

    Every formulation obtained is written, including the ones the validity filter
    excludes, each carrying the reason. That is what makes the filter auditable
    rather than merely asserted.
    """
    paths.FORMULATIONS.mkdir(parents=True, exist_ok=True)
    exclusions = json.loads((clean / "per_run_exclusions.json").read_text())

    written = excluded = 0
    with paths.FORMULATIONS_JSONL.open("w") as out:
        for responses_path in sorted(run_dir.glob("BANCO-*/run_*/responses.json")):
            vignette = responses_path.parent.parent.name
            run_name = responses_path.parent.name
            run_id = int(run_name.split("_")[1])
            payload = json.loads(responses_path.read_text())
            marks = exclusions[f"{vignette}/{run_name}"]
            absent, degenerate = set(marks["absent"]), set(marks["degenerate"])

            for response in payload["responses"]:
                model = response["id"]
                if model in absent:
                    status = "absent"
                elif model in degenerate:
                    status = "degenerate"
                else:
                    status = "analysed"
                if status != "analysed":
                    excluded += 1
                record = {
                    "vignette_id": vignette,
                    "run_id": run_id,
                    "model": model,
                    "status": status,
                    "framework_order": payload["order"],
                    "finish_reason": response.get("finish"),
                    "prompt_tokens": response.get("pt"),
                    "completion_tokens": response.get("ct"),
                    "reasoning_tokens": response.get("rt"),
                    "text": response.get("content") or "",
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1
    print(f"  {paths.FORMULATIONS_JSONL.name}: {written} records ({excluded} not analysed)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path,
                        help="internal run directory holding BANCO-*/run_*/")
    parser.add_argument("--bank", type=Path, required=True,
                        help="case bank JSON, read for design labels only")
    args = parser.parse_args()

    clean = args.run_dir / "_analysis_clean"
    print("indices:")
    export_indices(args.run_dir, clean)
    export_strata(args.bank)
    print("formulations:")
    export_formulations(args.run_dir, clean)


if __name__ == "__main__":
    main()
