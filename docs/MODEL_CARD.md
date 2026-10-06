# Model card

## Intended use

Educational prediction of movement before clearance within 60 simulated minutes after a stop is applied. A score prioritizes review; it never overrides a HOLD/REJECT. Deterministic rules handle confirmed violations. This is not a validated screening, customs, safety or carrier decision system.

## Simulation

18,000 unique packages generated using seed 42 across 60 simulated days and eight facilities. Inputs available at hold time include queue load, staffing, prior scan counts, time since last scan, scheduled departure, route hops, weight, hour, service, stop source and condition. Queue and staffing are simulated contextual metadata, not fields inferred from future scans. Historical scan features are reconstructed from events strictly before the hold.

A noisy latent bypass process depends on several operational factors and an unobserved random factor. Future movement and release times are sampled; the binary label is derived by replaying those future events: movement occurs while the stop remains active, within 60 minutes. The label is not directly assigned from an exported score. Full generator code is visible, so results reflect learning a designed synthetic process and can be optimistic. There is no empirical evidence that the relationships describe real logistics behavior.

The separate scripted 1,000-package handout fixture contains precisely 500 screening HOLD events, 300 brokerage HOLD events and 50 movement-after-hold scenarios. It is only a rules/integration demo and never trains the model. The 3,000-package stress set (seed 99) adds unseen facilities F8/F9 and a hidden increase in noncompliance. Facility identity is excluded from model inputs. No facility-specific random effects or real facility transfer are established.

## Evaluation

One snapshot per package. Fit days <40, validation days 40–49, test days >=50. No package ID repeats between splits. The chronological split is correct, but the main simulator is stationary; later-day evaluation is not evidence of resilience to real temporal drift. Compare prevalence, logistic regression and histogram gradient boosting. Select by validation average precision, reported precisely as average precision rather than accuracy. Tune each model threshold separately on validation with assumed false-negative cost 8 and false-positive cost 1. A departure-time heuristic flags departure within 20 minutes.

Risk scores are uncalibrated. Brier score measures probability error; calibration itself is not guaranteed. Threshold cost is an educational per-package assumption, not measured financial loss. Permutation importance on validation is model dependence, not causal evidence. Package bootstrap interval resamples test snapshots 300 times; excludes generator/model-selection uncertainty. Feature range warnings detect some unusual values but are not a drift monitor. Future test feedback must not be used to imply an untouched final test after subsequent model tuning.

## Operational limits

Scoring at the time a stop is applied; no retraining scheduler or calibrated updating hazard model. Real equipment telemetry is unrelated to this model. All future outcomes are simulated. High false-positive burden should be assessed against inspection capacity before any real use. Counterfactual UI adjustments can form unrealistic context combinations and do not estimate the causal effect of changing staffing. No prevented escapes, measured dollar savings or delivery improvements.

## Next work

Approved timestamped carrier event data and historical context; censoring and delayed labels; package/site-disjoint forward validation; calibration; review-budget top-k metrics; prediction updates that incorporate elapsed hold time; persistent operational UI and identity/access control. This project currently does not claim those features.
