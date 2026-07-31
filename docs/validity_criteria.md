# Formulation validity criteria

**Date:** 2026-07-28

## Background

The preregistered protocol for missing data specified that, when a model returned no usable formulation for a run, the call was to be retried up to four times, and if no usable formulation was obtained after the retries, the similarity matrix and the indices were to be computed from the voices that were available. The validity check actually implemented during execution verified only that the returned response was non-empty. In consequence, a response that was non-empty but degenerate (for example a stream of a single repeated character, a fragment truncated by a provider error, or text in the wrong language) passed the filter and was embedded and analysed as if it were a usable formulation, without triggering the retry rule.

This document freezes, after the fact, a mechanical operationalisation of "usable formulation". It defines eight criteria, each with an exact threshold, that together decide whether a formulation is degenerate. The criteria are applied uniformly to all seven thousand one hundred and sixty formulations that entered the analysis. They are stated here so that the classification can be reproduced exactly and so that no formulation is judged by anything other than these fixed rules. No index is recomputed and no data are regenerated as part of freezing these criteria; this document records the definition, and its application is reported separately.

A formulation is classified as degenerate if it meets **any** of the eight criteria below.

## The eight criteria

1. **Provider error.** The response carries a finish reason equal to `error`.

2. **Zero output.** The response has zero completion tokens.

3. **Too short.** The response contains fewer than 150 whitespace-delimited words. The instruction template requests a formulation of six hundred to eight hundred words with a fixed four-part structure; a response under 150 words cannot contain that structure and is treated as truncated or degenerate.

4. **Wrong language.** The predominant language of the response, as returned by the `langid` language detector, is not Spanish (`es`). The domain, the instruction template and the vignettes are in Spanish. The detector was verified on a sample of four hundred and eight legitimate formulations (each at least 150 words, finished normally), on which it returned Spanish in every case, so the criterion does not flag legitimate Spanish text.

5. **No framework declaration in the requested form.** The response does not contain the framework declaration in the format the template requests, as determined by the pipeline's framework parser (`extraer_marco_declarado_detallado`, field `extraccion_estructural_ok = False`; the parser's regular expression does not locate the "Leo este caso desde un marco [X]" declaration). A declaration that is present but names a framework outside the canonical set does **not** meet this criterion: it is a legitimate declaration of a non-standard framework, not a structural failure. This criterion uses the same parsing logic already used elsewhere in the pipeline; no new heuristic is introduced.

6. **Single-character repetition.** A single non-whitespace character accounts for more than 50 per cent of the non-whitespace characters of the response. In natural Spanish prose no single non-whitespace character exceeds about 15 per cent, so 50 per cent is a wide margin that flags character floods without touching ordinary text.

7. **Repeated n-gram loop.** A repeated word n-gram, for n equal to one, two or three, covers more than 35 per cent of the word tokens; that is, the most frequent n-gram, multiplied by n, exceeds 35 per cent of the total number of tokens. Natural prose repeats no n-gram beyond roughly 10 per cent coverage, so 35 per cent is a wide margin that flags looping repetition without touching ordinary text.

8. **Anomalous non-alphabetic proportion.** Non-alphabetic characters account for more than 40 per cent of the non-whitespace characters of the response. Natural Spanish prose is between about 85 and 90 per cent alphabetic among its non-whitespace characters, so a non-alphabetic proportion above 40 per cent is a wide margin that flags symbol floods without touching ordinary text.

## Blindness of the filter

None of the eight criteria uses the per-model dissent contribution, the spectral dissent index, the effective number of voices, or the identity of the model that produced the response. The filter is therefore blind to the magnitude of the dissent a formulation carries and blind to which model produced it. It decides only whether a response is a usable formulation on mechanical, content-level grounds.

## Revision, 2026-07-29

The eight criteria above were fixed on 2026-07-28 and then applied to the seven thousand one hundred and sixty formulations. Applying them showed that one of the eight was untenable. This section records the change and its reason, so that the order, criteria first and adjustment afterwards, is explicit and the adjustment is not made silently.

**Criterion 5, the absence of a framework declaration in the requested form, is withdrawn.** Of its fifty-four flags, thirty-four were legitimate and complete formulations whose framework was declared in a variant surface form that the exact-phrase parser does not recognise: a Markdown heading in deepseek-v4-flash ("# Lectura desde un marco …") and a bold label in minimax-m3 ("**Marco:** …"). The remaining twenty flags are genuine degenerate fragments, and each of them is caught by at least one other criterion, so criterion 5 contributes no unique true positive. It is withdrawn rather than relaxed: rewriting the criterion to admit the variant forms after seeing which formulations it catches would be an adjustment made after the observation, whereas withdrawing it makes the filter more conservative, which is the correct side on which to err. The operative filter is therefore the seven criteria numbered 1 to 4 and 6 to 8.

**The thresholds of the seven remaining criteria are unchanged, including the 150-word threshold of criterion 3.** That threshold flags four formulations that are coherent but short. It is retained nonetheless. The threshold was fixed before the filter was applied, and a response of, for example, thirty-four words, compared by semantic similarity against formulations of some seven hundred, introduces a length confounder in addition to failing the requested format; either reason is sufficient to treat such a response as not usable.

**The two formulations in which the character set changed part way through generation are counted as degenerate.** In both, minimax-m3 injected non-Latin characters mid-formulation, and the language detector classifies the complete text as outside Spanish; they are retained as failures of criterion 4.

This revision was made before any data were regenerated and before any index was recomputed.
