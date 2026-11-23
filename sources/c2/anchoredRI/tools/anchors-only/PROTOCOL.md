# Task A, Step 1: anchors-only comparator protocol

Status: Step A approved by the user and completed. Step B authorized by the user and specified below before execution. The original Step A execution gate is retained as historical documentation.
Prepared: 22 November 2026 (America/New_York).

## Question and scope

Does frozen anchoredRI improve reference interval accuracy over a parametric estimator using the same 40 healthy anchors alone?

Use the existing 45 scenarios and 20 replicates per scenario, for 900 paired evaluations. Do not change any file in R/ or tools/stress-design.R. Add study code only under tools/anchors-only/ after approval. This is a follow-up analysis of an already inspected simulation grid, not independent validation or a retrospective claim of preregistration.

## Inputs and pairing

For each case 1 through 45 and replicate 1 through 20, obtain d <- stress_data(case, replicate) from the unchanged design. The anchors-only fit receives only d$anchor, with exactly 40 observations. It must not receive routine measurements, service labels, disease prevalence, true limits, or the other 360 screened observations.

The oracle additionally receives the known family and, for shifted-lognormal data, the true offset of 10. This privileged information is exclusive to the oracle and makes it a diagnostic benchmark, not a deployable comparator or guaranteed minimum-error estimator.

Use the archived anchored40 full-data estimates from the completed 900-dataset comparison (GitHub Actions run 45074750888, source commit e6af4e02c0053931ef3d024f091e3200129d8493). The published archive is assets/comparison-study/summary/comparison-results.zip. Do not substitute the earlier replicate-1 bootstrap estimates. Join on case and replicate; verify dataset seeds, true limits and the complete 45-by-20 grid. Record archive checksum and source hashes. Do not retune or rerun anchoredRI for this task.

Anchors are reused across the 15 scenarios within each family and replicate. Thus there are 60 distinct anchor samples, scored in 900 paired rows. Anchors-only estimates must be identical across those 15 scenarios. Each scenario still has 20 independent replicates. Do not treat all 900 anchors-only rows as independent observations.

## Estimators

### A. Oracle anchors-only

Let a be the 40 anchors. Use the true family's transformation:

- Normal: y = a, inverse g(y) = y.
- Lognormal: y = log(a), inverse g(y) = exp(y).
- Shifted lognormal: y = log(a - 10), inverse g(y) = 10 + exp(y).

Calculate the arithmetic mean and sample SD on that scale, with SD denominator n - 1. Return g(mean(y) - 1.96 * SD(y)) and g(mean(y) + 1.96 * SD(y)). Use the requested constant 1.96 exactly. Flag an invalid transform domain, nonfinite estimate or nonpositive SD as a failed estimate. Do not clip or replace invalid values.

### B. Automatic anchors-only: primary comparator

Fit one Gaussian distribution on each eligible scale: identity, log, and shifted-log. This is not a mixture model. Selection uses BIC on the original measurement scale and n = 40.

For each fixed transformation, estimate mu by mean(y) and sigma by the maximum-likelihood SD, sqrt(mean((y - mean(y))^2)), for the likelihood and BIC calculation. The maximized original-scale log likelihood is:

- Identity: sum(log normal_density(a; mu, sigma)).
- Log: sum(log normal_density(log(a); mu, sigma)) - sum(log(a)).
- Shifted log at offset c: sum(log normal_density(log(a - c); mu(c), sigma(c))) - sum(log(a - c)).

BIC = -2 * maximized log likelihood + k * log(40), where k = 2 for identity/log and k = 3 for shifted-log. The estimated offset counts as a parameter even if its optimum lies on a bound. Include the Jacobian for every transformed observation. Log is eligible only if every anchor is positive.

For shifted-log, use anchor-derived bounds only:
[min(a) - 5 * MAD(a), min(a) - 0.001 * MAD(a)].
MAD means R's default normal-consistent mad(a), centered on the median (constant 1.4826). Do not use the routine-data MAD or the oracle offset. If MAD is zero or nonfinite, mark this candidate unavailable; do not silently replace the prescribed bounds.

Profile out mu and sigma analytically at every offset. Search the full bounded interval using a deterministic 1,001-point grid, refine every grid-local maximum between its neighboring grid points with bounded one-dimensional optimization, and compare those optima with both endpoints and all grid values. This avoids assuming that the profile is unimodal. Use an offset tolerance of 1e-8 * max(1, bound width). Record the selected offset, candidate BICs, and whether the optimum is within that tolerance of a bound.

Select the eligible candidate with the smallest finite BIC. BIC ties within 1e-8 are resolved in the fixed order identity, log, shifted-log. There is no outcome-driven override. A failed candidate remains recorded; if no candidate is valid, the automatic estimator fails.

After selecting the transformation and offset, calculate limits using mean(y) +/- 1.96 * sample SD(y), then back-transform. This uses the same n - 1 SD convention as the oracle for interval construction. The maximum-likelihood SD is used only for likelihood maximization and BIC; the distinction is explicit and fixed before running.

### C. Optional Horn robust estimator

Omitted from Step 1. It is not needed to answer the primary question. Adding a Horn/CLSI EP28 implementation would require a separately specified algorithm and verified reference implementation before results are examined.

## Scoring and metadata

Use the unchanged stress_metrics() for all endpoint and tail metrics, through stress_row(), on each of the 900 evaluations per estimator. The existing stress_row() method-name handling assumes its original methods. A study-local wrapper will call it with compatible direct40 metadata, then set the descriptive method identifier to anchors_oracle or anchors_auto. Retain n_routine = 0 and n_screened = 40; set components = 1 and record transformation, offset, bound flag, elapsed time and errors. Do not modify the shared scoring functions.

Primary error E is width_error:
100 * max(abs(estimated lower - true lower), abs(estimated upper - true upper)) / (true upper - true lower).

Retain the other stress_metrics() fields: signed lower and upper error, mean percentage endpoint error, fractions below and above the estimated interval, healthy reference coverage, the exploratory error >10% flag, and status. Reference coverage is the population fraction inside the estimated interval, not confidence-interval coverage. No bootstrap confidence intervals are computed in Step 1.

Report attempts, successful fits, failed fits and bound hits. Retain all failed rows. A profile-boundary optimum is flagged but is not automatically a failure.

## Paired analysis

For each scenario and replicate r define:
D_r = E_anchoredRI,r - E_auto,r.

Negative differences favor anchoredRI. With all 20 valid pairs, report:

- Mean(D), median(D), and the two methods' mean errors.
- Paired wins for anchoredRI (D < 0), ties (D = 0), and wins for auto (D > 0).
- Monte Carlo SE = sample SD(D_1, ..., D_20) / sqrt(20).
- Attempted and valid pair counts, failures by method, and auto boundary counts.

If any pair fails, retain it in the attempted denominator and label that scenario's primary decision indeterminate. Descriptive finite-pair differences may be shown with their actual denominator, but do not apply the 20-pair decision rule to a reduced sample.

Oracle results are secondary and descriptive. They do not determine the primary decision or the automatic fit.

## Decision rule

Apply the user's rule separately to every separated and moderate-overlap cell:

Routine data add value in that cell if
mean(D) + 2 * MCSE(D) < 0.

Equivalently, anchoredRI's paired mean error must be lower than auto's by more than two Monte Carlo standard errors. The inequality is strict; equality does not qualify.

There are 30 primary cells: 3 families x 2 overlap levels x 5 affected fractions. Report the decision in every cell and counts meeting the rule by family and overlap. Do not replace this with a pooled overall mean or select favorable cells after seeing results. No additional all-cells or majority-cells rule for a global superiority claim is imposed.

Show the 15 heavy-overlap cells as descriptive stress results, labeled outside the primary decision rule. Report whether their paired differences favor anchoredRI or auto without using them to redefine the primary criterion.

This is the specified Monte Carlo evidence rule, not a multiplicity-adjusted significance test or a clinical acceptance threshold. MCSE measures simulation precision. Shared anchors across scenarios preclude treating cell summaries as independent evidence in an aggregate test.

## Deliverables after approval

1. Complete estimator-level CSV with 900 rows each for oracle and auto, plus the matched anchoredRI estimates or an explicit linked paired file.
2. Candidate-fit diagnostics, selected transformations, offsets and boundary flags.
3. Scenario-level paired CSV with differences, wins, MCSE and decision labels.
4. One 3 x 5 overlap-by-affected table per family. Rows: separated, moderate, heavy. Columns: 10%, 30%, 50%, 70%, 90%. Each cell shows paired mean difference, 2 * MCSE, wins out of 20, and the decision label (or descriptive-only for heavy overlap).
5. A brief interpretation of where routine data add value over the automatic parametric anchors-only estimator, with oracle performance as context.

## Execution gate

This commit contains the protocol only. Stop and show it to the user before writing implementation code, generating datasets, fitting estimators, running tests or launching workflows for Task A. Resume only after the user's review authorizes the next step.

## Step B: disagreement check (specified before execution)

Step A was approved and completed. This extension is authorized by the Step B request. Freeze the following rules before examining Step B results.

For each of the 900 datasets, resample its 40 anchors with replacement 1,000 times. Repeat the entire auto estimator, including BIC family selection and shifted-log offset profiling, in every resample. Use percentile 2.5% and 97.5% quantiles (R type 7) separately for the lower and upper limits. These are marginal intervals, not a simultaneous 95% confidence region. Identical anchor samples across scenarios may share a bootstrap calculation after exact equality is verified. Seeds are 19400000 + 10000 * family index + replicate; generate all resample indices before fitting.

Primary flag: either original anchoredRI endpoint lies strictly outside its corresponding bootstrap CI. Equality with a CI endpoint passes. When flagged, return no reference interval. Recommend at least 120 screened patients or verification of a suitable published interval with 20. Retain anchoredRI and anchors-only estimates, and both CIs, as diagnostics only. Never substitute the anchors-only interval. When unflagged, return the original anchoredRI interval unchanged. An invalid anchoredRI interval or any failed bootstrap fit makes the check unavailable and causes a decline, recorded separately from a statistical flag. Require all 1,000 fits; do not silently discard failures.

Secondary check: use the anchoredRI transformation and offset, held fixed. Infer component-1 Gaussian mean and SD from its stored endpoints using qnorm(0.975). Compare the anchors' log likelihood at these parameters with their own Gaussian maximum-likelihood mean and SD on that same scale. The Jacobian is identical and cancels. Statistic = 2 * (own-fit log likelihood - component-1 log likelihood); nominal p = upper-tail chi-squared probability with 2 df. Flag strictly at p < 0.01. Invalid transformed anchors make this check unavailable. This is an exploratory diagnostic: transformation selection and reuse of anchors in fitting mean its nominal p-value is not guaranteed calibrated. It does not override the primary rule, and does not select a different transformation or re-estimate the offset.

Report both checks separately by family, overlap, and affected fraction, plus pooled 3 x 5 overlap-by-affected tables. Denominators and counts accompany flag rates, proportions of original anchoredRI >10%-error datasets flagged, proportions of original anchoredRI <5%-error datasets flagged, unavailable counts, decline rates, and error of retained intervals (mean, median, 90th percentile, maximum, and >10% proportion). Error is the existing stress_metrics worst endpoint error divided by true interval width, in percent. Threshold comparisons are strict. An empty denominator is reported as unavailable. Primary declines include unavailable checks; secondary hypothetical declines include its flags and unavailable checks and are labeled separately. Shared anchor samples imply dependence between scenario rows; pooled percentages are descriptive.

Keep B=1,000, marginal 95% CIs, p<0.01, and the 10%/5% reporting thresholds unchanged. If any threshold changes after results are inspected, confirm the revised rule on fresh replicates 21–40, including new anchoredRI fits. Do not claim confirmation from the original 20 replicates. No threshold changes are planned. Production R/ and tools/stress-design.R remain unchanged.
