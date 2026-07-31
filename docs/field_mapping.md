# Field mapping

The published data use English field names. The study's internal artifacts, from
which the manuscript was written, use Spanish ones. This table records the
correspondence so that any number in the manuscript can be traced to a column
here, and vice versa.

Nothing was recomputed in renaming: `src/export_data.py` copies values across and
changes only the names.

## `data/indices/ensemble_indices.csv` — one row per run (450)

| Published | Internal | Meaning |
|---|---|---|
| `vignette_id` | `vineta_id` | vignette identifier, `BANCO-001` … `BANCO-015` |
| `run_id` | `run_id` | run within the vignette, 1 … 30 |
| `s_norm` | `S_norm` | normalised von Neumann entropy of the spectrum, in [0, 1] |
| `n_eff` | `N_eff` | effective number of voices (the Vendi Score), in [1, n] |
| `condition_number` | `cond` | ratio of largest to smallest eigenvalue |
| `n_voices` | `n_voces` | valid voices contributing to the run |

## `data/indices/per_model_dissent.csv` — one row per analysed formulation (7,082)

| Published | Internal | Meaning |
|---|---|---|
| `vignette_id` | `vineta_id` | vignette identifier |
| `run_id` | `run_id` | run within the vignette |
| `model` | `model` | model identifier, in its familiar form |
| `d_i` | `d_i` | dissent contribution of that voice in that run |
| `n_voices_in_run` | `n_voces_corrida` | valid voices in the run the value comes from |

## `data/indices/run_exclusions.json` — one entry per run (450)

Keys were `BANCO-001/run_01` internally and are `BANCO-001/1` here, so the run
number matches the integer `run_id` of the CSV files. The four fields inside
(`n_valid`, `n_present`, `absent`, `degenerate`) were already in English.

## `data/indices/vignette_strata.csv` — design labels (15)

The bank's two crossed design dimensions, published without any vignette text.

| Published | Internal | Meaning |
|---|---|---|
| `vignette_id` | `case_id` | vignette identifier |
| `clinical_picture` | `grilla_primaria.cuadro` | clinical picture |
| `openness_stratum` | `grilla_primaria.apertura_interpretativa` | interpretive openness |

Value translations:

| Published | Internal |
|---|---|
| `depression` | `depresion` |
| `trauma` | `trauma` |
| `substance_abuse` | `abuso_de_sustancias` |
| `relational_conflict` | `conflicto_vincular` |
| `shared_frame_ineffective` | `marco_compartido_ineficaz` |
| `shared_frame_effective` | `marco_compartido_eficaz` |
| `genuinely_distinct` | `marco_genuinamente_distinto` |

## `data/indices/panel.csv` — the sixteen models

`model` is the identifier as it appears in the other data files;
`pinned_identifier` is the dated snapshot actually queried. `family`, `line`,
`scale_pair` and `scale_role` were derived from the panel configuration and are
the grouping used by the exploratory analyses.

## `data/formulations/formulations.jsonl` — every formulation obtained (7,200)

New file; there is no internal equivalent, since the formulations were held as
450 directories of `responses.json`. Field origins:

| Published | Internal | Meaning |
|---|---|---|
| `vignette_id` | directory name | vignette identifier |
| `run_id` | directory name | run number, as an integer |
| `model` | `responses[].id` | model identifier |
| `status` | derived from `per_run_exclusions.json` | `analysed`, `degenerate` or `absent` |
| `framework_order` | `order` | the run's presentation order of the ten frameworks |
| `finish_reason` | `responses[].finish` | provider finish reason |
| `prompt_tokens` | `responses[].pt` | prompt tokens |
| `completion_tokens` | `responses[].ct` | completion tokens |
| `reasoning_tokens` | `responses[].rt` | reasoning tokens, zero throughout by design |
| `text` | `responses[].content` | the formulation itself |

## What was deliberately not translated

The therapeutic framework labels stay in Spanish (`apego`,
`trauma somático/sensoriomotor`, and so on). They are data rather than
identifiers: the models were shown a Spanish menu and their replies quote it, so
an English label would not be what the model wrote. The formulations themselves
are in Spanish for the same reason. `src/framework_parser.py` documents the ten
labels and maps declarations onto them.
