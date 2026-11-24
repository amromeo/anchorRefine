# anchorRefine study protocol

Stages 0 and 1 are complete and accepted. Stage 2 development is approved under the three amendments below. Report development and the selected K before opening confirmation.

## Purpose and boundaries

Develop a derivative of refineR 2.0.0 that fits a healthy Box–Cox distribution to the central portion of routine data, without fitting a pathological distribution, and uses 40 independently screened healthy observations per test set. This repository is separate from anchoredRI. Do not edit, push to, or run jobs in the anchoredRI repository.

First review this protocol. After approval, implement and freeze Stage 0, run it, and stop to show its results. Stage 1 requires approval of the Stage 0 report. Stages 2 and 3 remain plans until separately approved. Every amendment must be committed before affected runs, with its reason and whether any relevant outcomes have already been seen. Never silently replace a failed run or change a threshold after inspecting results.

## Source, license, and attribution

The package will use `License: GPL-3`. Vendor the complete, unmodified refineR 2.0.0 source archive and its extracted source after protocol review, preserving upstream license, author, copyright, citation, and bundled third-party notices. Keep a pristine copy separate from derivative implementation files. Mark modifications and retain provenance for copied functions. Keep a permanent pass-through mode that executes the pristine algorithm unchanged, including upstream defaults and numerical behavior.

The upstream DESCRIPTION identifies Matthias Beck, Tatjana Ammer, Christopher M Rank, and Andre Schuetzenmeister as authors. Preserve these credits; do not represent upstream authors as maintainers of this derivative. State prominently in README and package documentation: “anchorRefine is derived from refineR 2.0.0. It is an independent project and is not endorsed by the refineR authors.”

Source inspected, without executing it:

- URL: https://cran.r-project.org/src/contrib/refineR_2.0.0.tar.gz
- Version: 2.0.0; upstream license: GPL (>= 3).
- SHA-256: `c9ffc7a42f81d6a40e2448504673e57defeaf03d7d1f72f3acd64a6f3e8fc02a`.
- The archive URL under `src/contrib/Archive/refineR/` returned 404 at inspection. Preserve the downloaded bytes rather than relying on a mutable URL.

The initial documentation commit contained no upstream code. After protocol approval, the exact archive and extracted source were vendored under `vendor/`; original notices are retained.

## Required inputs and freeze before runs

The source project is `amromeo/amromeo.github.io`, directory `anchoredRI/`. C2 run 45096614442 and its source history have been located and preserved. See [docs/SOURCE_REVIEW.md](docs/SOURCE_REVIEW.md) for immutable revisions, source hashes, parameter availability and remaining execution prerequisites.

Before Stage 0, commit an input manifest specifying:

1. RIbench source version/commit, data archive hashes, exact test-set Index values, sample sizes, scenario/replicate identities, true healthy distributions and reference limits, and pathological fractions. Include every available set with N <= 5,000. Stage 1 additionally includes every set with N = 50,000. Never choose subsets by observed performance.
2. C2 run identity, anchoredRI commit, archived refineR output paths and hashes, invocation/options, RNG settings, and all comparator versions. Record whether full-precision limits and fitted Mu, Sigma, Lambda, Shift were saved. A rounded table alone is insufficient for an exact check.
3. The anchoredRI anchor generator, its source hash, R RNG kinds/version, screening rule, sampling method, and data source. Use exactly 40 new healthy observations per Index with seed `17000000 + Index`. Seed alone does not establish identical anchors: verify their ordered values or hashes against C2. Never sample anchors from the routine dataset, reuse one anchor panel across sets, or pool anchors across test sets. All methods within a test set use the same anchor panel.
4. The exact archived z-score formula, endpoint scaling, anchors-only estimator, and implausibility rules. These are not available yet and must not be guessed. Commit their formulas and source locations before execution. If archived definitions cannot be recovered, stop and obtain approval of explicit replacements; label subsequent comparisons as non-identical.
5. Source SHA-256 hashes for upstream, derivative code, benchmark runner, scoring functions, dependencies/lockfile, anchor generation, and input files. Record Git commit, R version, platform, BLAS/LAPACK, locale, thread settings, package versions, seeds, and command lines. Freeze execution settings and the per-Index ordering before results.

Verify the manifest against files at run start and end. Archive full precision machine-readable results, fit objects, warnings/errors, logs, timings, and checksums. Changes require a new manifest/run ID. Source inspection and schema inspection are allowed before runs; benchmark fitting and performance summaries are not.

## Reproducibility rules for every stage

Same-machine checks and cross-machine audits are separate gates. Neither substitutes for the other.

On one machine, run reference and candidate paths in isolated R sessions with identical inputs, order, options, dependency versions, RNG state and thread settings. Require bitwise-identical numeric outputs (including limits and all fitted parameters), identical missing-value categories, and matching fit status. Compare substantive fit fields with zero tolerance; separately enumerate metadata such as elapsed time, call text, or environment addresses that cannot be identical. Never exclude fitted results from comparison as metadata. Repeat the frozen stage run on that machine; p-values, scores, and decisions must also match exactly. Failed fits remain in the inventory.

For a separate machine, use the same frozen artifacts and settings and record hardware/software differences. For every finite RI, require each endpoint difference <= 0.001 times the reference interval width. For Stage 0 the reference is the archived C2 refineR interval. Nonpositive/nonfinite reference width or missing reference is non-auditable, never a pass. Fit status must agree. For Stage 1 also require absolute p-value difference <= 0.0001 and decision agreement; a threshold crossing is a discrepancy even if p-value tolerance passes. Report parameter differences but judge RI equivalence by endpoints, since parameters can have different numerical sensitivities. Audit all eligible sets; report missing coverage explicitly.

If no genuinely separate machine/archive exists for a new stage, mark that audit pending and do not claim complete reproducibility. Any mismatch, missing required source, manifest drift, or non-auditable required row blocks progression pending a documented investigation and user review. Preserve original results and any reruns separately.

## Stage 0: reproduce refineR

Question: does the pass-through implementation reproduce CRAN refineR 2.0.0?

Install CRAN refineR 2.0.0 from the frozen archive in a separate library. Build the pass-through path from the pristine vendored copy. Use C2's exact invocation, including model choice, bootstrap settings, RI percentiles, point-estimate convention and preprocessing, once recovered. Do not silently use modern defaults if C2 differed. Both paths receive identical routine observations; anchors are unused.

Run both paths on all RIbench N <= 5,000 sets. Require exact same-machine agreement as defined above on every row. Matching failures establish matching behavior but are still counted as failures. A new failure or mismatch fails Stage 0.

For the exact comparisons, use native refineR getRI() with its full-data point estimate. For the historical audit, use RIbench 1.0.2 getRI(truncNormal = FALSE), as in C2, on new and archived fits. Compare new limits to the archived, full-precision C2 limits. Report the native versus historical extraction difference on the same fit separately. For CRP compare only the 95th percentile, using its archived upper limit minus zero as width. For the other nine analytes use the 2.5th and 97.5th percentiles and the archived upper minus lower limit. Apply the 0.1%-of-archived-width tolerance to each requested endpoint. Keep same-machine results and cross-machine results in separate tables. Diagnose source/options/input/version differences before attributing disagreement to hardware.

Deliver: frozen manifest; expected/completed/missing row counts by N; exact-match counts; failures and warnings; per-endpoint cross-machine absolute and width-normalized differences; every tolerance violation; and source/license provenance. Stage 0 passes only when all required exact checks and cross-machine audits pass. Stop and show the report before Stage 1.

## Stage 1: anchors as a check

The routine-data fit and returned RI remain unchanged. Anchors only determine whether to keep or decline a fit. A kept result must be numerically identical to its ungated refineR result. No refitting based on anchor compatibility, replacing declined limits, or selecting a different peak is allowed in this stage.

### Fit reuse

Use archived refineR fits if all four parameters (Mu, Sigma, Lambda, Shift), exact options, input identity, full precision, and provenance are available and verified. Validate reconstructed limits against archived limits. If parameters are absent or incomplete, refit the affected sets with the Stage 0 validated path and frozen settings. Never infer four parameters from two reference limits. Record `archived` or `refit` per row. Evaluate both N <= 5,000 and N = 50,000; keep the sample-size groups separate.

### Approved Stage 1 decisions

1. Report both native refineR getRI (Box–Cox support corrected) and historical RIbench 1.0.2 getRI(truncNormal = FALSE) for every fit, including fits the check declines. Use the **historical extraction as primary for all comparisons** with anchoredRI and anchors-only. Report native refineR as a labeled secondary analysis. The same fitted parameters and anchor decisions apply to both extractions.
2. The C2 anchors are rounded to RIbench decimals. Use randomized PIT within each rounding interval. In anchor draw order use independent uniforms with R seed 38000000 + Index. Repeat the check with 39000000 + Index on the identical anchors. Report both decisions per dataset, the keep-to-decline and decline-to-keep counts, and the share of paired decisions that change. Show failures and denominators.
3. Compare against archived C2 anchoredRI, labeled **old fitter**, and archived anchors-only. Present Task E improved-fitter results as a separate row for each cohort whose export is complete and whose dataset and anchor identities match. Proceed using C2 wherever the Task E export is incomplete. Use the raw Task E estimate for estimator comparisons and identify any reported safeguard results separately.
4. Run on GitHub Actions. Gate the N ≤ 5,000 analysis on null calibration, then the N = 50,000 analysis on the completed small-cohort technical checks. Present the Stage 1 results for review before any Stage 2 work.

### Likelihood-ratio test

Use a location-and-spread likelihood-ratio test in the fitted model's probability scale. It tests compatibility with the complete fitted model through its CDF, which depends on mu, sigma, lambda and shift. It is not a four-parameter refit to 40 anchors and is not an omnibus shape test.

Let F0 be the healthy CDF from the frozen refineR fit. For a recorded anchor a_i at step h = 10^(-decimals), evaluate L = F0(a_i - h/2) and H = F0(a_i + h/2). Draw v_i from Uniform(0,1), set u_i = L + v_i (H - L), and use y_i = Phi^{-1}(u_i). Use stable lower/upper log probabilities in the tails. Under a continuous latent model rounding ties have zero probability. For supported nonnegative shifts, conditioning on the screened support x >= 0 is already satisfied. Under the fixed-model null the 40 y_i are independent N(0,1). The alternative is y_i ~ N(m,s²), with free location and positive variance. Equivalently its density on the original scale is f0(a) phi((y-m)/s)/(s phi(y)); the change-of-variable terms cancel in the likelihood ratio.

With n = 40, m_hat = mean(y), and v_hat = mean((y-m_hat)²), use:

`T = 2 (log L_alt - log L_null) = n * (m_hat² + v_hat - 1 - log(v_hat))`.

Use the finite-sample null distribution. Under H0, A = n*m_hat² ~ chi-square(1) and V = n*v_hat ~ chi-square(n-1), independently, so T = A + V - n - n*log(V/n). Compute its survival probability by deterministic one-dimensional integration over V, with requested absolute error <= 1e-10. The integrand is the chi-square(39) density times the chi-square(1) survival probability at `T - V + n + n*log(V/n)`, taking that survival probability as 1 when its argument is nonpositive. Validate this calibration using independent null simulations before benchmark scoring, under committed validation code and seeds. Do not substitute chi-square(4), or asymptotic chi-square(2), for the primary p-value.

Decline exactly when p < 0.01. Keep p = 0.01. No across-set multiplicity adjustment: the decision is per proposed reference interval, and the benchmark measures its operating characteristics. A p-value assesses a fixed fitted model conditional on the routine-data fit; it does not integrate uncertainty in that fit.

### Support and numerical conventions

Use refineR's actual subtraction convention x - Shift. For positive lambda, transformed support is y > -1/lambda; the normal density/CDF must be normalized on this support. At lambda = 0 use the logarithmic transform and untruncated normal. Use stable tail/log-probability calculations rather than rounding a positive tail probability to zero or clipping u to an arbitrary epsilon.

Inspection of `R/utils.R::cdfTruncatedBoxCox` found a separate negative-lambda branch and clipping of negative/invalid reported limits to zero. Before execution, document the supported fitted parameter range and reconcile the healthy CDF, truncation, and any censoring with this exact upstream implementation. A negative-lambda or censored distribution must not be silently treated as an ordinary continuous normal transform. If such fits occur in the frozen configuration, stop for a committed protocol amendment before applying the LRT to them. The validation must cover the actual supported range without changing pass-through behavior.

A rounding bin whose entire interval is outside true model support gives a structural incompatibility: record p = 0 and decline, with its own reason code. Arithmetic underflow is not evidence of support violation. Degenerate transformed anchors, unavailable parameters, invalid sigma, CDF/integration failure, and unresolved rounded/censored anchor behavior are `check_failed`, not significant tests. They receive no accepted RI and are reported separately from statistical declines. Missing/invalid anchors are not replaced using routine observations. A rounded value at the support boundary remains valid when its bin has positive model mass. The randomized PIT rule above supplies the calibrated test for the coarsened observations.

### Calibration and reproducibility gates

Before evaluating RIbench decisions, run 100,000 independent panels of 40 for each design below. Draw under the fitted null including truncation, apply the measurement rounding, then run the randomized PIT under both seeds. The simulated panels include valid bins that overlap the support boundary. Evaluate at 0.01 and 0.05, using the exact finite-sample null critical values for the statistic specified above. Independently verify the numerical survival calculation and its decision near the cutoffs.

| Design | Mu | Sigma | Lambda | Shift | Decimals |
|---|---:|---:|---:|---:|---:|
| Fine log | 1 | 0.4 | 0 | 0 | 3 |
| Coarse log | 0 | 0.8 | 0 | 0 | 0 |
| Truncated linear | -1 | 0.8 | 1 | 0 | 0 |
| Shifted, grid of 10 | -2 | 0.55 | 0.5 | 2 | -1 |

Number the synthetic Index from 1 to 400,000 in table order. Seed latent draws with 36000000 + Index. For all sixteen design-by-seed-by-alpha checks require the count to fall within the inclusive binomial quantiles 0.00005 and 0.99995 for B = 100,000 and the given alpha. Any failed calibration check stops benchmark execution. The screened reference model in this stage supports nonnegative shift and lambda with positive sigma. Flag unsupported fits and surface them for review.

For each cohort, run the identical cases twice in isolated R processes on one Actions runner and again on a separate runner. Verify distinct machines, frozen input hashes and exact same-host results. For the cross-machine audit require identical check status and decision under each PIT seed, absolute p differences ≤ 0.0001, and differences at each requested endpoint ≤ 0.001 times the first host's width, using the upper limit as width for CRP. Report statistic differences. Check the identity of each retained endpoint against the original refineR limit. Archive fits or their immutable source, both probabilities and decisions, estimates and reproducibility records. Technical failures block progression. Performance is descriptive at this stage.

### Comparators and reporting

Compare refineR alone, refineR with the anchor check, anchors-only using the recovered C2 definition and the identical 40 anchors, and the existing anchoredRI result versions. Verify paired Index/input identities and anchor hashes. Unmatched or differently generated comparisons must be labeled and excluded from paired contrasts, with their counts shown. Never rerun or modify anchoredRI in its repository.

Report separately for N <= 5,000 and N = 50,000, and within each for pathological fraction <= 20% versus > 20%. Also show individual N and scenario strata. Weight test sets equally within each primary stratum; show scenario-balanced sensitivity summaries if replicate counts differ.

Using the frozen C2 endpoint z definition, let E = max(|z_lower|, |z_upper|). Primary bad-result capture is the proportion of valid baseline fits with E > 1 that are statistically declined; repeat for E > 5. Good-result loss is the proportion with E < 0.25 that are statistically declined. Use strict inequalities; show boundary counts. Also report endpoint-level versions so an interval with one bad limit cannot be hidden by averaging.

Report statistical decline rate among evaluable checks, overall non-return rate among all planned sets, baseline fit failures, check failures, and structural incompatibilities separately. Report counts with every denominator. Failed checks do not count as successful bad-result detection. Show both the conditional capture among evaluable tests and capture among all valid baseline bad fits.

For kept results, report signed endpoint bias, mean/median |z|, capped mean |z|, E quantiles (50th, 90th, 95th, 99th), and proportions E > 1 and E > 5. The primary cap is fixed at 5: per-set loss = (min(|z_lower|,5) + min(|z_upper|,5))/2. If C2 used another cap, reproduce it as a separately labeled historical metric; do not replace the primary cap after seeing results.

Show comparator accuracy on the same kept Index set as well as on each method's full available set. The kept refineR limits must have exactly the same accuracy as ungated refineR restricted to those indices. Any apparent improvement is selection, not improved estimation. Include coverage-versus-error tables and assign loss 5 to a missing/failed/declined result in a separate all-set sensitivity summary so abstention cannot disappear from the denominator. Do not present this failure-penalized measure as accuracy of kept estimates.

Provide 95% uncertainty intervals for rates and paired loss differences, clustering by RIbench parent scenario when multiple replicates share one scenario. Use (Analyte, Scenario) as the parent cluster. Within each reported stratum draw the observed clusters uniformly with replacement, using identical cluster counts for each method, extraction and seed. Use percentile intervals at 2.5% and 97.5%, reporting undefined replicates and suppressing CIs for fewer than two clusters. Use 2,000 paired cluster bootstrap resamples with NumPy PCG64 seed 37000000; show raw counts and descriptive intervals without claiming population-level generalization beyond RIbench.

Stage 1 has no invented performance pass threshold. It passes technical validation only if inputs, calibration, exact preservation of kept fits, reproducibility and audits pass. Present the full usefulness results, including false declines, for user review. Stop before Stage 2 regardless of whether results look favorable.

## Stages 2 and 3

### Stage 2 approved development protocol

**Question.** Can 40 screened healthy measurements identify the healthy peak and improve refineR’s reference limits when more than 20% of the routine sample is pathological? Stage 2 guides the routine-data search. The routine histogram supplies the fitted model’s cost. There is one final fit per method and dataset. The 40 anchors remain separate from the routine sample.

**Primary extraction for Stages 2 and 3.** Use native refineR 2.0.0 `getRI` with its Box–Cox support correction for **every success gate**, for both candidate and baseline. Report the C2 historical formula, RIbench 1.0.2 `getRI(truncNormal = FALSE)`, as a labeled secondary analysis on the same fits. At N ≤ 5,000 in Stage 1, 42 refineR fits had E > 5 under the historical extraction and 18 under the native extraction. The extractor alone changed which errors counted as severe. The support-corrected limits are the output we intend to evaluate going forward. Stage 1 retains its historical-primary analysis. [Stage 1 results](results/stage1-45276858699/analysis/REPORT.md)

#### 1. Choose a routine-data peak

1. Use the Stage 0 plain Box–Cox fit with shift 0 and no bootstrap. Make the initial choice at the **first raw-scale** `findMainPeak` call in `estimateAB`, on upstream’s 512-bin average shifted histogram (ASH), before trimming or constructing the cost histogram. Use the routine peaks and valleys detected by upstream. For adjacent peaks use the intervening detected valley with lowest density (leftmost on an exact tie). Use the ASH window edges for the two outer boundaries. An absent intervening valley, missing peak, zero-width basin or nonfinite density makes guidance unavailable. A basin is its interval between boundaries. An interior boundary belongs to the basin on its right. The final right edge is included.
2. Let h be the recorded anchor rounding increment. Each of the 40 anchors casts at most one vote. Count it for a basin only if its full possible measurement interval [a − h/2, a + h/2), intersected with the positive measurement support, lies in that basin. A cell crossing a valley or extending outside the ASH window casts no vote. An empty intersection casts no vote. Keep 40 in the denominator. Use finite nonnegative anchors on the declared grid in their original draw order. Compute raw anchor quantiles with R type 7.
3. A clear winner must have at least **K of 40 votes**, lead the runner-up by at least **8**, and have its coarse peak location inside the anchors’ inclusive 10th-to-90th percentile interval. Use zero runner-up votes for a single peak. A tie or failure of any condition invokes the fallback below. An isolated mixture peak can pass this rule even when disease overlaps it. The development set explicitly tests that case. The only candidate choices are K = 24 and K = 28. Section 4 fixes how to choose one before RIbench.
4. For peak guidance, record the winning raw basin and use its peak index for that first coarse choice. At every subsequent coarse or fine peak choice in `estimateAB` and in both per-lambda passes of `defineSearchRegions`, restrict the detected routine peaks to those inside that raw basin. On a transformed grid compare in Box–Cox coordinates by mapping the basin endpoints to the working scale, taking the positive-domain limit at zero. Among eligible peaks choose the one closest to the median of the anchors that voted for the winning basin, transformed to the current scale. Break exact ties by larger routine density, then lower grid index. The median is computed on raw anchors before transformation. A nonfinite target or no eligible peak triggers fallback. This tracks a basin across transformations while allowing its modal location to move.
5. After each index choice use upstream’s three-bin interpolation, 35%-height local window, smoothing, and subsequent histogram/width calculations. A peak change can therefore change both the histogram endpoints (`abHist`) and the routine window for parameter estimation (`abSearchReg`). Score each search on its own resulting routine histogram. The rule never chooses between peak windows by comparing costs on different histograms. [Vendored search and density code](vendor/refineR/R/algoInvHist.R)

#### 2. Set initial values and search regions

For each lambda on both upstream passes, apply its Box–Cox transformation T to the type-7 quartiles of **all 40** anchors. Use m = T(Q50) and s = [T(Q75) − T(Q25)] / 1.3489795003921634. These are location and scale proposals for the grid. The histogram fit estimates Mu and Sigma. Require positive Q25, three finite transformed quartiles, and s > 0. Compute each proposal deterministically without PIT jitter.

| Component | Operation when active |
|---|---|
| Starting values | For active bounds [L,U] and anchor proposal c (m for Mu, s for Sigma), put one node at c. For j = 1 through k, put nodes at c − (c−L)(j/k)² and c + (U−c)(j/k)². Use k = 4 for Mu and k = 6 for Sigma, yielding nine and thirteen sorted nodes, including the exact endpoints. This puts more of the first grid near the anchor proposal even when c lies at the midpoint. If c is on or outside the active bounds, retain the upstream equally spaced nodes on that axis. Collapsed or nonfinite nodes make that guided grid unusable. |
| Search regions | Use [m − 1.5s, m + 1.5s] for Mu and [s/2, 2s] for Sigma in place of the per-lambda routine-derived intervals. These are hard bounds for this component. On later iterations project each adaptive grid coordinate to its nearest bound if outside, sort, and remove duplicates. Require a finite, positive-width initial interval on each axis and positive Sigma. If a projected refinement produces no new coordinate on either axis, finish that lambda with its incumbent. |
| Routine optimization | Use upstream’s 13-point first lambda grid, its 12-point refinement about the winning lambda and up to seven Mu/Sigma grid iterations per lambda. Retain upstream’s objective, healthy-fraction search, strict cost-improvement rule and iteration order. With search regions off, upstream’s adaptive grid can extend past its initial endpoints. |

#### 3. Fallback, ablations and anchor check

Compute the initial clarity decision once using the same prepared routine data for every arm. Preserve upstream’s routine jitter draws and RNG state. If the anchors, declared precision or first peak election are unusable, run the original pass-through from the original input and RNG state. Also use this whole-fit fallback if an **active** component cannot produce its required basin, finite proposal or usable grid, or the guided fit errors or fails to return ResultFound with finite Mu, Sigma, Lambda and Shift and positive Sigma. Do not select a second candidate using cost, PIT p-value or truth. Record the failing step, reason and resulting pass-through status. Count fallback in its assigned arm. If pass-through also fails, count a fit failure. A valid single peak can support start or region guidance even when the peak choice itself agrees with upstream.

| Arm | Peak | Starting nodes | Search regions |
|---|---|---|---|
| Baseline, unmodified refineR | Upstream | Upstream | Upstream |
| Peak choice only | Anchor-selected | Upstream | Upstream |
| Starting values only | Upstream | Anchor proposals | Upstream |
| Search regions only | Upstream | Equally spaced | Anchor bounds |
| Full Stage 2 candidate | Anchor-selected | Anchor proposals | Anchor bounds |

The three ablations use the selected K and the same confidence decision and paired inputs as the full candidate. Only the enabled operation changes the fit. Changes to a histogram or an upstream width estimate that follow from changing the peak belong to the peak-only effect. Verify that switching all components off, or taking fallback, reproduces pass-through exactly on the same machine.

**Before and after the check.** Retain both sets of limits from every valid fit in every arm, including fallback. Then apply the frozen Stage 1 rounded-anchor check to that fit using the same 40 anchors, rounding precision and strict p < 0.01 decision. Use both PIT seeds as in Stage 1 and the primary seed for release. A decline withholds both endpoint extractions. Record fit failure and check failure separately. Report coverage, error, declines, good results lost, bad results caught and seed reversals, with the Stage 1 definitions. The check uses all 40 anchors that were also available to guide the search. For an adaptive fit its p-value is a compatibility score. The 1% false-decline calibration from Stage 1 applies to a correct model fixed independently of the check panel. Estimate actual decline behavior in the simulations.

#### Stage 2 candidate decision after the development ablations

The user fixed this decision on 2026-11-24 after reviewing the three K = 24 ablations. Use the archived development fits at commit 193c802. Include every dataset with a clear K = 24 election whose detected peak index differs from the upstream index on the same first raw-scale 512-bin density. Pool both pathology strata, all six disease patterns, healthy families, rounding increments and replicates within each routine N. For unchanged refineR, peak choice only and full K = 24, report the arithmetic mean of the pre-check native loss defined below, including the existing loss of 5 for an unreturned interval.

Use option B only if the full search has strictly lower mean loss than peak choice alone at both N = 1,500 and N = 50,000. Under option B, a clear different peak uses the full K = 24 search and a clear identical peak uses unchanged refineR. Otherwise select the existing K = 24 peak-choice-only arm on every dataset. Both choices preserve the existing fallback and Stage 1 check. Apply the rule to the unrounded means. Commit the choice, reason and source hashes before rerunning the selected implementation once on development. Verify the expected per-dataset results against the existing fits. Successful reproduction permits opening the eight fresh confirmation replicates per factorial cell. Run the candidate, three ablations and unchanged refineR, report the existing confirmation gates and stop before RIbench.

#### 4. Independent development and confirmation data

After plan approval, build a **new synthetic dataset**, with no RIbench generator, analyte settings, case data, templates, fits or outcome tables. Use a known healthy CDF H. For a healthy latent score Z ~ N(0,1), generate the measurement X = H-inverse(Phi(Z)). Use the same map for disease scores. Define H by a normal on the Box–Cox scale with the indicated Mu and Sigma, conditioned on the valid transform support and inverse-transformed with shift zero. Use native H quantiles at 0.025 and 0.975 as truth before measurement rounding.

| Factor | Prespecified levels |
|---|---|
| Healthy family (lambda, Mu, Sigma) | (0, log(10), 0.35), (1, 12, 1), and (0.5, 4, 0.75), in that order. In the linear family the median is 13 to machine precision. The power-0.5 family puts the transformed lower boundary at −2, eight SDs below Mu. |
| Routine sample size | 1,500 and 50,000 |
| Pathological fraction | 0.25, 0.45 and 0.60 for the development target. Use separate control cells at 0.10 and 0.20. |
| Disease score (mean, SD) | Left separated (−3, 0.7), right separated (+3, 0.7), left shoulder (−0.65, 0.9), right shoulder (+0.65, 0.9), bilateral separated (equal mixture of the two separated distributions), and overlapping at the healthy center (0, 1.6). |
| Assay rounding increment | 0.05 and 0.25 times the population SD of the unrounded healthy measurement in original units for that family. Compute this SD under H including its support correction. Round to h × round(x/h) using R ties-to-even for both routine and anchor measurements. Use this same h for the PIT bin edges. |
| Replicates per factorial cell | Four for development, eight fresh replicates for confirmation |

Cross all levels. Draw exactly N times the stated pathological fraction from the designated disease distribution, the remainder from H, then shuffle the routine vector. In the bilateral case assign half of disease draws to each side, with an odd extra draw on the right. Draw 40 healthy anchors independently per dataset. Draw a second independent panel of 40 **only for a simulation diagnostic**. Apply the check to the already fitted model using that fresh panel and report how often reusing the guidance panel changes the decision. For each panel and both PIT seeds report the share of baseline or candidate errors caught at E > 1 and E > 5 and the share with E < 0.25 declined, using the corresponding pre-check fit and Stage 1 denominator rules. Pair decisions within dataset and fit. Only the original 40 determine the fit and the primary release decision.

Enumerate cells in table order, in the listed order within each row, with replicate varying fastest. Number development datasets from j = 1 and confirmation datasets separately from j = 1. Use integer seeds 62000000 + 10j + k (development) and 72000000 + 10j + k (confirmation), with k = 0 for routine draws and shuffle, 1 for guidance anchors, 2 for the diagnostic anchors, 3 for the routine fitter, and 4 and 5 for the primary and alternate PIT randomizations. Use 6 and 7 for the diagnostic panel’s two PIT randomizations. Freeze the R RNG kinds used in Stage 1. This gives 864 target and 576 control datasets for development (1,440 total), then 1,728 target and 1,152 controls for confirmation (2,880 total, kept unopened during development). Freeze and hash the generator, truth and seed manifest before generating data. Keep component labels and truth accessible only to scoring. Hash ordered routine vectors and panels, and pair them across arms.

**Choice and independent check.** Run the two full K candidates and the baseline on development data only. Compute each dataset’s native endpoint error in healthy standard-normal units, Phi-inverse(H(truth)) minus Phi-inverse(H(estimate)). Map out-of-support limits to their CDF boundary and count them separately. Apply the same cap of 5, equal weighting and missing-result loss as in the benchmark. Rank K by the smaller worst of its two N-specific differences from baseline in mean **pre-check** capped loss on the >20% development cells. On an exact tie choose K = 28. This selects the fitter on the accuracy of the intervals it estimates. Also report controls, implausible counts, fallback, and results after the check for both candidates. Commit the chosen K, code, hashes and development report **before opening confirmation**. On confirmation run the one selected candidate, the three ablations and baseline once. Report all strata, including overlapping disease and controls, before RIbench. Report which targets the confirmation results meet and retain the prespecified candidate for the benchmark. A change to the rule requires a documented amendment, new source freeze and fresh confirmation data before evaluation. RIbench is reserved for evaluating the frozen candidate. Its results cannot select or revise the rule.

#### 5. RIbench analysis and reproducibility

After development and confirmation, freeze the candidate, sources, environment, code for all arms, input manifest, decision rules and reporting code before any RIbench run. Use the Stage 0/1 frozen routine vectors or their hash-verified regeneration and independently screened panels (40 per Index, anchor seed 17000000 + Index, PIT seeds 38000000 + Index and 39000000 + Index). Use the same routine fitter seed and settings across paired arms. Evaluate on GitHub Actions, small cohort first, then N = 50,000 after the small technical audit. Include every planned Index. Report the unchanged refineR baseline before its check and its Stage 1 release on the same indices.

For each arm report the fitted intervals **before checking** and the released intervals **after checking** at both pathological-fraction strata and both sample-size groups. Show raw counts, denominators, kept-set accuracy, and all-dataset loss with 5 for each missing result. **Judge Stage 2 on the pre-check candidate fit versus unchanged, ungated refineR** using the fixed gates below. Charge a fit failure, including failed fallback, loss 5. **Judge the checked release separately against refineR with the same Stage 1 check** on the same guidance anchors and primary PIT seed. Apply the same criteria, counting declines and other nonreturns as loss 5 on both sides. Show checked candidate versus ungated refineR in a descriptive table only. Report both judgments separately. The fresh panel is a simulation diagnostic and never determines actual release.

For the implausibility gate use the archived RIbench definition, an **uncapped mean absolute endpoint z above 5** within a dataset (CRP has one endpoint). Show E > 5, nonfinite, out-of-support and unordered limits separately. Report these counts on raw fits as well as releases so a decline cannot conceal an implausible fit. Use paired percentile intervals clustered by (Analyte, Scenario) as in Stage 1. In the synthetic study cluster by factorial design cell, with replicates together. Report the same-host exact comparisons and a distinct-host tolerance audit on every planned set. Check parameters, raw and released endpoints, scores, peak choice, fallback, both PIT p-values and decisions. Use the existing endpoint tolerance of 0.1% of reference width and absolute p-value tolerance of 0.0001 on the separate host, require matching decisions and branch choices, and report all discrepancies. Stop for review after Stage 2.

### Stage 3

Before coding, show a source-grounded derivation of `calculateCostHist` and a proposed common scale for the anchor term. The inspected code uses overlapping histogram bins, predicted counts normalized over the histogram range, a searched healthy fraction P, relaxation factor rf, selected bins within prediction bands, and multiplicative peak/tail penalties. For K selected bins, predicted counts cPred and scaled observed counts cData, its implemented cost is:

`C = -[sum(log(sqrt(P*rf/(2*pi))*sqrtCountsPred)) + K*(log(ratioCounts80)+log(ratioCounts20L)+log(ratioCounts20R)) - 0.5*sum((cData-cPred)^2/cPred)]/sqrt(K)`.

Selection, K, P, rf and penalties can vary with the candidate. This is a regularized, scaled histogram objective with dependent overlapping bins; it cannot automatically be treated as an ordinary independent-observation negative log-likelihood. Simply adding 40 anchor log densities would leave their relative weight unjustified.

The required Stage 3 proposal must specify the proper Box–Cox anchor density (including Jacobian and support normalization), the objective sign, a common reference measure/scale, how bin overlap and candidate-dependent K are handled, and the fixed weight. It must demonstrate behavior under unit changes, binning changes, and N changes. Weight zero must reproduce the preceding frozen algorithm exactly. Choose any calibration using separate simulations, not the RIbench evaluation outcomes. Show the derivation and decision rules for approval before implementation or runs.

### Fixed success criteria for each of Stages 2 and 3

Use native refineR limits for both sides of every Stage 2 and Stage 3 success gate. Keep historical C2 limits as a labeled secondary analysis. Evaluate the Stage 2 fitter and checked release against their respective baselines as specified above. Evaluate Stage 3 against unchanged refineR. Apply each gate separately at N <= 5,000 and N = 50,000. Stage 3 also reports its paired difference from Stage 2. Success requires all of the following in both sample-size groups:

- At > 20% pathological: strictly lower primary capped mean |z| than refineR.
- At <= 20% pathological: candidate minus refineR capped mean |z| <= 0.02.
- No greater count of implausible results than refineR in either pathological-fraction stratum, using the recovered C2 definition above. Report the separate endpoint and invalid-interval flags. Any additional clinical plausibility rule needs a source and a pre-run freeze.

The cap is 5 and endpoint/test-set aggregation is defined above. For these success decisions, failures and non-returned intervals receive loss 5, all planned sets stay in the denominator, and a candidate may not reduce its implausibility count by dropping results: report failures/nonreturns separately and require their count not to increase. Report paired uncertainty intervals; the stated numerical gates use point estimates, not an undeclared significance test. A claim that all gates were met requires complete paired coverage and reproducibility audits. Failure of any gate means the stage has not met the prespecified target. Stop and show results before further work.

## Review gate

The user approved the Stage 2 plan with three amendments on 2026-11-23, before generating any development or confirmation data. The amendments pair like-for-like success comparisons, move the simulated healthy families away from their support boundaries and scale rounding to healthy SD, and measure bad-result capture and good-result loss for both anchor panels. Implement and freeze the generator and search rules, run development, then stop and show the chosen K and development report before opening confirmation. Stage 3 still requires a written common-scale objective and separate approval. The original Stage 0 and Stage 1 manifests apply at their respective run commits.

### Stage 1 execution record

In [run 45276328667](https://github.com/amromeo/anchorRefine/actions/runs/45276328667), the null calibration and both small-cohort evaluation jobs completed. The independent audit stopped while reading the original RIbench inventory because the out-of-scope 500,000-sample records express N as `5e+05`. The large cohort did not run. Before retrying, the audit reader was corrected to interpret numeric N in either ordinary or scientific notation. The corrected reader selects 2,880 small and 1,440 large records from the frozen specification. Calibration pass status was known. No RIbench performance summaries had been inspected. The fit, test, seeds, inclusion criteria, audit thresholds and reporting rules are identical in both runs. Preserve the initial run and repeat all stages of the Stage 1 workflow.
