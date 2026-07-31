# Deviations from the Preregistration

**Date:** 2026-07-22

This document records the deviations from the sealed preregistration (osf.io/c5qk7) that were adopted for the execution of the study. **All decisions described below were made before any data from the model panel were generated.** The preregistration remains the record of the confirmatory commitment; these deviations are documented transparently and do not alter the hypotheses, the definition of the dissent index, or the analysis plan.

## Note on the manuscript title (identification, not a deviation)

The manuscript carries a title different from the one under which the study was registered. For unambiguous identification, both are reproduced here.

**Registered title (sealed preregistration, osf.io/c5qk7):** "The Clinical Dissent Index as a model-level confidence instrument: a spectral characterization across a heterogeneous panel of large language models in psychotherapeutic formulation".

**Manuscript title:** "Sixteen models, fewer than two voices: measuring ensemble dispersion where no answer is uniquely correct".

This is the fourth manuscript title. Three earlier ones were carried in draft: "Measuring when a language model ensemble has no single answer: effective diversity as a trigger for meaningful human oversight"; the same title with "candidate signal" in place of "trigger"; and "Sixteen models, fewer than two voices: effective diversity in a language model ensemble on psychotherapeutic case formulation". The third was adopted after a post-hoc analysis, reported in the Results, found that dissent does not track the interpretive openness for which the case bank was stratified, so presenting the measure as a signal for oversight would have overstated what the study supports. The fourth was adopted on recognising that both literatures which measure this quantity validate it against a correctness criterion that the present task does not admit, which is what the study characterises.

**Note on the headline figures.** The title states two numbers: an effective voice count of 1.69 and a single-model baseline of 1.43. The first is the measured value of the registered response variable. The second is not part of the registered commitment: the single-model self-consistency baseline is a descriptive calibration computed after the data were generated, under a seed fixed at the time it was computed, and no such baseline was registered. It is labelled post-hoc where it is reported, in the Results and in section S8 of the Supplementary Material, and is recorded here because the two figures carry the title together.

The two titles name the same study. The hypothesis, the definition of the dissent index, the composition of the panel, and the analysis plan are those registered, and none of them changed with the title. This is recorded here as an identification note, so that the manuscript and the preregistration can be matched, and not as a methodological deviation: the preregistration commits the confirmatory hypothesis, the measure, and the analysis plan, and does not commit the title, so a change of title is not a departure from it.

## Execution deviations

Two deviations were adopted. Both arose from provider-level constraints discovered during a pre-execution verification of the panel and were resolved so as to preserve, as closely as possible, the equivalence of effective conditions across models that the study requires.

## Deviation 1. The panel comprises 16 models rather than 17

**Preregistered.** A panel of seventeen language models.

**Executed.** Sixteen models. One model, `openai/gpt-oss-120b`, was excluded.

**Rationale.** This model requires internal reasoning by design and does not permit it to be disabled: requests that set reasoning to disabled were rejected with an explicit provider error ("Reasoning is mandatory for this endpoint and cannot be disabled"), and this held across every available provider for the model. Retaining it would have introduced generative reasoning in a single voice while the other fifteen reasoning-capable models had reasoning disabled, creating an asymmetry of treatment across the panel that is incompatible with a controlled comparison of model contributions to dissent.

**Supporting evidence and impact.** The exclusion is clean with respect to the study's design structure: the excluded model was the second member of its family, which the exclusion leaves represented by a single model, and it does not belong to any of the four within-family scale pairs used in the exploratory scale analysis, so its removal breaks no scale comparison. The panel remains a heterogeneous set of sixteen models drawn from multiple families.

## Deviation 2. Maximum output length raised from 2048 to 4096 tokens

**Preregistered.** A maximum of 2048 output tokens per formulation.

**Executed.** A maximum of 4096 output tokens per formulation.

**Rationale.** At 2048 tokens, two models produced clinical formulations that were cut off mid-sentence rather than completed. A truncated formulation contaminates the dissent measure with an artifact of the length limit: the embedding of an incomplete text differs systematically from that of a complete one, so the measured separation between voices would partly reflect where each response happened to be cut rather than genuine clinical divergence. Because the object of measurement is the dispersion among complete formulations, allowing every voice to finish is a precondition for the measure to be valid.

**Supporting evidence.** With a limit of 2048 tokens, both affected models terminated by reaching the length limit rather than by completing (their responses ended at the token cap). With a limit of 3072 tokens or greater, both terminated by completion, producing full formulations of approximately 2040 to 2740 tokens. A limit of 4096 tokens was adopted to provide a comfortable margin above the longest observed complete formulation. Critically, the models that already completed within 2048 tokens were verified to behave identically at 4096: they continued to terminate by completion with equivalent output lengths, confirming that raising the limit affects only the previously truncated responses and does not alter the behaviour of the rest of the panel.

## Clarifications (not deviations)

**Reasoning disabled to preserve equivalence with the reference condition.** The preregistration establishes that generation parameters are held identical to the earlier reference condition on which the design draws. Reasoning was therefore disabled (`reasoning: {enabled: false}`) on the reasoning-capable models for which it can be disabled cleanly, in order to preserve that equivalence of effective parameters. Disabling reasoning is a measure to maintain the preregistered equivalence, not a departure from it.

**One model emits a reasoning field with no effect on the data.** The model `google/gemini-3-flash-preview` attaches a reasoning field to its response regardless of the parameter setting; however, this field carries zero billed reasoning tokens and the response content itself is a normal clinical formulation. Because the analysis pipeline embeds only the response content and never the reasoning field, this behaviour affects neither the measured dissent nor the cost. The model is used as delivered, and this is recorded here as a clarification rather than as a deviation.

## Execution notes

The full run comprised 450 runs per model over the fixed vignette bank (fifteen vignettes, thirty presentation orders each). Three aspects of the executed dataset are recorded here for transparency. None was corrected post hoc, and no analysis was performed in producing this record.

**Missing voices.** In 40 of the 450 runs, one voice was absent: under the disabled-reasoning setting the model returned an empty or insufficient response and therefore contributed no formulation to that run. Of these absences, 38 involved a single model (`minimax-m3`) and 2 involved another (`glm-5.2`); the remaining fourteen models contributed a formulation in all 450 runs. The absences were not uniformly distributed but concentrated in a contiguous window of the run sequence spanning four consecutively processed vignettes, consistent with a transient provider instability rather than a property of any vignette, and they subsided thereafter: eight of the fifteen vignettes have no missing voice at all. The preregistered missing-data rule was applied as specified: each affected run was retried, and where a voice remained absent after retries the run's index was computed from the available fifteen voices, with the reduced voice count and the identity of the absent model recorded for that run. No post-hoc recovery of the missing voices was attempted, because re-running only the runs known to have failed would constitute a non-preregistered procedure applied selectively to the failures and would generate data in a different temporal window from the rest of the dataset. The affected runs are retained as executed.

**Residual truncation at the raised limit.** With the output limit set to 4096 tokens (Deviation 2), 47 of the 7200 voice-level responses (0.65%) still reached the limit and terminated by length rather than by completion. These are the most verbose formulations in the panel; the residual is minor and is reported here for completeness.

**One recomputed embedding.** In a single run, all sixteen models produced a formulation, but one of the sixteen responses exceeded the 8192-token input limit of the embedding model, so the run's embeddings could not be computed on the first pass. They were recomputed by truncating that run's responses more aggressively than the rest of the dataset (to 6000 characters rather than the standard 8000) so that the over-length response fit the embedding model's limit. This single run therefore carries embeddings generated under a slightly different truncation than the other 449; the difference is recorded here and in the dataset manifest.
