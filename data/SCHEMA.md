# Data schema

Five files. Every field name is English and matches the names used in `src/`; the
correspondence with the study's internal artifacts is in
[`docs/field_mapping.md`](../docs/field_mapping.md).

The vignette bank itself is **not** included here. See the README.

## `indices/ensemble_indices.csv`

One row per ensemble run. 450 rows (15 vignettes x 30 presentation orders).

| Field | Type | Description |
|---|---|---|
| `vignette_id` | string | `BANCO-001` … `BANCO-015` |
| `run_id` | integer | 1 … 30 within the vignette |
| `s_norm` | float | normalised von Neumann entropy of the spectrum, in [0, 1]; higher is more dissent |
| `n_eff` | float | effective number of voices, the Vendi Score, in [1, n] |
| `condition_number` | float | largest over smallest eigenvalue of the similarity matrix |
| `n_voices` | integer | valid voices in the run (14, 15 or 16) |

`n_eff = n_voices ** s_norm`.

## `indices/per_model_dissent.csv`

One row per analysed formulation. 7,082 rows.

| Field | Type | Description |
|---|---|---|
| `vignette_id` | string | vignette identifier |
| `run_id` | integer | run within the vignette |
| `model` | string | model identifier |
| `d_i` | float | dissent contribution: 1 minus the mean similarity of that voice to the rest of its run |
| `n_voices_in_run` | integer | valid voices in that run |

## `indices/run_exclusions.json`

Object keyed by `"<vignette_id>/<run_id>"`, 450 entries.

| Field | Type | Description |
|---|---|---|
| `n_valid` | integer | voices analysed |
| `n_present` | integer | voices that returned a formulation |
| `absent` | list of string | models that returned nothing usable |
| `degenerate` | list of string | models whose formulation failed the validity filter |

## `indices/vignette_strata.csv`

The bank's design labels, one row per vignette. 15 rows. Published so that the
stratified analyses can be reproduced without the clinical material.

| Field | Type | Values |
|---|---|---|
| `vignette_id` | string | `BANCO-001` … `BANCO-015` |
| `clinical_picture` | string | `depression`, `trauma`, `substance_abuse`, `relational_conflict` |
| `openness_stratum` | string | `shared_frame_ineffective`, `shared_frame_effective`, `genuinely_distinct` |

## `indices/panel.csv`

The sixteen models. 16 rows.

| Field | Type | Description |
|---|---|---|
| `model` | string | identifier as used in the other files |
| `pinned_identifier` | string | dated snapshot actually queried |
| `family` | string | provider taxonomy |
| `line` | string | finer taxonomy; the two Gemini generations and the two Gemma models are distinct lines |
| `scale_pair` | string | name of the within-family scale pair, empty if none |
| `scale_role` | string | `small` or `large` within that pair, empty if none |

## `formulations/formulations.jsonl`

One JSON object per line, one line per formulation obtained: **7,200** records,
that is 16 models x 450 runs. Roughly 41 MB.

| Field | Type | Description |
|---|---|---|
| `vignette_id` | string | vignette identifier |
| `run_id` | integer | run within the vignette |
| `model` | string | model identifier |
| `status` | string | `analysed` (7,082), `degenerate` (78) or `absent` (40) |
| `framework_order` | list of string | the run's presentation order of the ten frameworks |
| `finish_reason` | string | provider finish reason (`stop`, `length`, `error`) |
| `prompt_tokens` | integer | prompt tokens |
| `completion_tokens` | integer | completion tokens |
| `reasoning_tokens` | integer | reasoning tokens; zero throughout, reasoning was disabled |
| `text` | string | the formulation, in Spanish; empty for absent voices |

Formulations excluded by the validity filter are included, carrying their status,
so the filter can be audited rather than taken on trust. The analyses consume
only the records with `status == "analysed"`.

The formulations are in Spanish, as are the framework labels the models declare:
the instruction template and the vignettes were Spanish, and translating either
would misrepresent what the models produced.

## Not published here

**Embeddings.** The similarity matrices were built from `text-embedding-3-large`
embeddings of the formulations. These are not included; they can be regenerated
from `formulations.jsonl` with any embedding model, though the published index
values correspond to that one.

**The vignette bank.** Not included; see the README for the restricted deposit.
