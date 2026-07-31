> **Design document, frozen at registration.** This file is one of the four documents
> the sealed preregistration (osf.io/c5qk7) names as held in the project repository and
> released with the paper. It is reproduced here as it stood when the study was
> registered, and is not updated to match the executed study: it therefore describes a
> panel of **seventeen** models. One of them, `openai/gpt-oss-120b`, was excluded before
> execution because its reasoning could not be disabled, leaving the sixteen that were
> run. That exclusion is Deviation 1 in `deviations_from_preregistration.md`, which also
> records the second execution deviation and the departures adopted afterwards.
>
> For the same reason, the paths, file names and code references that appear in the body
> below belong to the project's internal working tree as it stood at registration, not to
> this deposit: `analizador.py`, the helper scripts and the intermediate result files named
> here are not part of the released repository. They are kept because these documents are
> the record of how the index was defined and tested at the time, and rewriting their
> references would misrepresent that record. The released implementation of the index is
> `src/dissent.py`.

# Verification of models on OpenRouter — list of 17 (Farhad + 3 originals)

**Scope:** verification of the provider catalogue, blocking for the design. `modelos.json` is **NOT** verified; the delivered list of 17 strings is verified.
**Query date:** 2026-07-05
**Endpoints used:**
- `GET https://openrouter.ai/api/v1/models` (full catalog: 340 models) → existence, canonical id, context, price, `supported_parameters`, `expiration_date`.
- `GET https://openrouter.ai/api/v1/models/{slug}/endpoints` → number of live endpoints (providers).

> ⚠️ OpenRouter catalogs change frequently. Snapshot of **2026-07-05**. Re-verify before freezing the ensemble for production.
> ℹ️ This verification **supersedes** the previous one (which audited the 12 in `modelos.json`); that one is kept in `verificacion_openrouter_20260705_modelos_json_legacy.md`.

---

## Verdict: 17/17 exist with exact id ✅

**All 17 strings exist with the exact id**, all with **live endpoints**, all support **`temperature`** and **`max_tokens`**, and **none has a sunset** (`expiration_date = null`). **No string requires substitution.**

Relevant notes:
- The 2026-07-05 catalog already includes recent models (`qwen3.7-plus`, `grok-4.3`, `gemini-3-flash-preview`, `deepseek-v4-*`, `minimax-m3`, `glm-5.2`, `gemma-4-31b`).
- None of the 17 ids is a `:free` variant (none carries a `:free` suffix). **4** of them do have a `:free` variant available as a **separate** id in the catalog (see below).

---

## Main table

Price in **USD per 1M tokens** (in/out), as reported by `/models` for the default provider. `temp`/`max_tok` = support for `temperature` / `max_tokens`.

| # | String (requested id) | Exact id exists | Live endpoints | Context | In /1M | Out /1M | temp | max_tok | Sunset | Has `:free` variant? |
|---|---|:---:|:---:|---:|---:|---:|:---:|:---:|:---:|:---:|
| 1 | `openai/gpt-4o` | ✅ | ✅ (2) | 128 000 | $2.50 | $10.00 | ✅ | ✅ | no | no |
| 2 | `anthropic/claude-sonnet-4.5` | ✅ | ✅ (7) | 1 000 000 | $3.00 | $15.00 | ✅ | ✅ | no | no |
| 3 | `google/gemini-2.5-flash` | ✅ | ✅ (4) | 1 048 576 | $0.30 | $2.50 | ✅ | ✅ | no | no |
| 4 | `mistralai/ministral-14b-2512` | ✅ | ✅ (2) | 262 144 | $0.20 | $0.20 | ✅ | ✅ | no | no |
| 5 | `mistralai/mistral-large-2512` | ✅ | ✅ (1) | 262 144 | $0.50 | $1.50 | ✅ | ✅ | no | no |
| 6 | `meta-llama/llama-3.3-70b-instruct` | ✅ | ✅ (12) | 131 072 | $0.10 | $0.32 | ✅ | ✅ | no | **yes** → `:free` |
| 7 | `qwen/qwen3.7-plus` | ✅ | ✅ (1) | 1 000 000 | $0.32 | $1.28 | ✅ | ✅ | no | no |
| 8 | `x-ai/grok-4.3` | ✅ | ✅ (2) | 1 000 000 | $1.25 | $2.50 | ✅ | ✅ | no | no |
| 9 | `google/gemini-3-flash-preview` | ✅ | ✅ (2) | 1 048 576 | $0.50 | $3.00 | ✅ | ✅ | no | no |
| 10 | `anthropic/claude-haiku-4.5` | ✅ | ✅ (5) | 200 000 | $1.00 | $5.00 | ✅ | ✅ | no | no |
| 11 | `google/gemma-4-26b-a4b-it` | ✅ | ✅ (10) | 262 144 | $0.06 | $0.33 | ✅ | ✅ | no | **yes** → `:free` |
| 12 | `deepseek/deepseek-v4-flash` | ✅ | ✅ (16) | 1 048 576 | $0.09 | $0.18 | ✅ | ✅ | no | no |
| 13 | `minimax/minimax-m3` | ✅ | ✅ (7) | 1 048 576 | $0.30 | $1.20 | ✅ | ✅ | no | no |
| 14 | `z-ai/glm-5.2` | ✅ | ✅ (28) | 1 048 576 | $0.574 | $1.804 | ✅ | ✅ | no | no |
| 15 | `deepseek/deepseek-v4-pro` | ✅ | ✅ (15) | 1 048 576 | $0.435 | $0.87 | ✅ | ✅ | no | no |
| 16 | `openai/gpt-oss-120b` | ✅ | ✅ (20) | 131 072 | $0.03 | $0.15 | ✅ | ✅ | no | **yes** → `:free` |
| 17 | `google/gemma-4-31b-it` | ✅ | ✅ (13) | 262 144 | $0.12 | $0.35 | ✅ | ✅ | no | **yes** → `:free` |

**Substitution candidates:** none needed (all 17 exist).

---

## Canonical `id` vs `canonical_slug`

**The invokable `id` matches the requested string exactly for all 17 → no string needs to be changed.** OpenRouter adds an internal dated `canonical_slug`, which is only an informational alias (not used in the calls). Those that differ from the `id`:

| id (invokable, = requested) | canonical_slug (informational, dated) |
|---|---|
| `anthropic/claude-sonnet-4.5` | `anthropic/claude-4.5-sonnet-20250929` |
| `qwen/qwen3.7-plus` | `qwen/qwen3.7-plus-20260602` |
| `x-ai/grok-4.3` | `x-ai/grok-4.3-20260430` |
| `google/gemini-3-flash-preview` | `google/gemini-3-flash-preview-20251217` |
| `anthropic/claude-haiku-4.5` | `anthropic/claude-4.5-haiku-20251001` |
| `google/gemma-4-26b-a4b-it` | `google/gemma-4-26b-a4b-it-20260403` |
| `deepseek/deepseek-v4-flash` | `deepseek/deepseek-v4-flash-20260423` |
| `minimax/minimax-m3` | `minimax/minimax-m3-20260531` |
| `z-ai/glm-5.2` | `z-ai/glm-5.2-20260616` |
| `deepseek/deepseek-v4-pro` | `deepseek/deepseek-v4-pro-20260423` |
| `google/gemma-4-31b-it` | `google/gemma-4-31b-it-20260402` |

(The rest — `openai/gpt-4o`, `google/gemini-2.5-flash`, `mistralai/ministral-14b-2512`, `mistralai/mistral-large-2512`, `meta-llama/llama-3.3-70b-instruct`, `openai/gpt-oss-120b` — have a `canonical_slug` identical to the `id`.)

> If one wanted to **pin the date** for maximum reproducibility, the dated `canonical_slug` could be used as the explicit id; but the base `id` (without date) is valid, stable, and is what was requested. Never use a `-latest` (floating) alias.

---

## `:free` variants and rate limit

Of the 17, **4 models have a `:free` variant** available as a **separate** id in the catalog (same base model, price $0, own endpoints):

| paid id (in the list of 17) | available `:free` id |
|---|---|
| `meta-llama/llama-3.3-70b-instruct` | `meta-llama/llama-3.3-70b-instruct:free` |
| `google/gemma-4-26b-a4b-it` | `google/gemma-4-26b-a4b-it:free` |
| `openai/gpt-oss-120b` | `openai/gpt-oss-120b:free` |
| `google/gemma-4-31b-it` | `google/gemma-4-31b-it:free` |

**Rate limit of the `:free` variants:** ⚠️ **Not reported in the API per model.** The `/models` and `/endpoints` objects do **not** include any rate-limit field (keys of an endpoint: `context_length, latency_last_30m, max_completion_tokens, max_prompt_tokens, model_id, model_name, name, pricing, provider_name, quantization, status, supported_parameters, supports_implicit_caching, tag, throughput_last_30m, uptime_last_1d, uptime_last_30m, uptime_last_5m`). The limits of the `:free` models are **global account policy** at OpenRouter (not per model): as of this date, on the order of **~20 req/min** and **~50 req/day** (expandable to **~1000 req/day** with ≥10 USD of lifetime purchased credits). Verify against the specific account before sizing runs.

> Note: querying `/endpoints` with the **base id** (without `:free`) returns only the **paid** endpoints; the free endpoints hang off the `:free` id, which is a distinct entry in `/models`.

---

## Methodology / reproducibility

```bash
# 1) Full catalog (public, no API key)
curl -s https://openrouter.ai/api/v1/models -o or_models.json   # 340 models on 2026-07-05

# 2) For each string: exact match of .id → context_length,
#    pricing.prompt/completion (×1e6 = per 1M), supported_parameters, expiration_date, canonical_slug

# 3) Live endpoints per model:
curl -s https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints | jq '.data.endpoints | length'
```

Criteria: **Exists** = `.id` identical to the string · **Sunset/deprecated** = `expiration_date` not null (all null) · **Live endpoints** = ≥1 endpoint · **temp/max_tok** = presence in `supported_parameters`.
