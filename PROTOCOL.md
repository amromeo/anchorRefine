# anchorRefine: stages 0–1 protocol

Status: proposed for review. No implementation or benchmark run is authorized by this document alone. Prepared 2026-11-23.

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

No upstream code is vendored in this initial documentation commit. The archive was downloaded only to a temporary inspection directory.

## Required inputs and freeze before runs

The anchoredRI repository and C2 artifacts are not currently accessible at `amromeo/anchoredRI`. Their location is a blocking prerequisite for benchmark execution, not a reason to substitute another experiment.

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

Independently compare the pass-through limits to C2 archived refineR limits with the 0.1%-of-archived-width endpoint tolerance. Keep same-machine results and cross-machine results in separate tables. Diagnose source/options/input/version differences before attributing disagreement to hardware.

Deliver: frozen manifest; expected/completed/missing row counts by N; exact-match counts; failures and warnings; per-endpoint cross-machine absolute and width-normalized differences; every tolerance violation; and source/license provenance. Stage 0 passes only when all required exact checks and cross-machine audits pass. Stop and show the report before Stage 1.

## Stage 1: anchors as a check

The routine-data fit and returned RI remain unchanged. Anchors only determine whether to keep or decline a fit. A kept result must be numerically identical to its ungated refineR result. No refitting based on anchor compatibility, replacing declined limits, or selecting a different peak is allowed in this stage.

### Fit reuse

Use archived refineR fits if all four parameters (Mu, Sigma, Lambda, Shift), exact options, input identity, full precision, and provenance are available and verified. Validate reconstructed limits against archived limits. If parameters are absent or incomplete, refit the affected sets with the Stage 0 validated path and frozen settings. Never infer four parameters from two reference limits. Record `archived` or `refit` per row. Evaluate both N <= 5,000 and N = 50,000; keep the sample-size groups separate.

### Proposed likelihood-ratio test

This protocol proposes a location-and-spread likelihood-ratio test in the fitted model's probability scale. It tests compatibility with the complete fitted model through its CDF, which depends on mu, sigma, lambda and shift. It is not a four-parameter refit to 40 anchors and is not an omnibus shape test. Approval of this protocol includes approval of this specific alternative hypothesis.

Let F0 be the healthy CDF from the frozen refineR fit. For each anchor a_i, set u_i = F0(a_i), y_i = Phi^{-1}(u_i). Under the fixed-model null the 40 y_i are independent N(0,1). The alternative is y_i ~ N(m,s²), with free location and positive variance. Equivalently its density on the original scale is f0(a) phi((y-m)/s)/(s phi(y)); the change-of-variable terms cancel in the likelihood ratio.

With n = 40, m_hat = mean(y), and v_hat = mean((y-m_hat)²), use:

`T = 2 (log L_alt - log L_null) = n * (m_hat² + v_hat - 1 - log(v_hat))`.

Use the finite-sample null distribution. Under H0, A = n*m_hat² ~ chi-square(1) and V = n*v_hat ~ chi-square(n-1), independently, so T = A + V - n - n*log(V/n). Compute its survival probability by deterministic one-dimensional integration over V, with requested absolute error <= 1e-10. The integrand is the chi-square(39) density times the chi-square(1) survival probability at `T - V + n + n*log(V/n)`, taking that survival probability as 1 when its argument is nonpositive. Validate this calibration using independent null simulations before benchmark scoring, under committed validation code and seeds. Do not substitute chi-square(4), or asymptotic chi-square(2), for the primary p-value.

Decline exactly when p < 0.01. Keep p = 0.01. No across-set multiplicity adjustment: the decision is per proposed reference interval, and the benchmark measures its operating characteristics. A p-value assesses a fixed fitted model conditional on the routine-data fit; it does not integrate uncertainty in that fit.

### Support and numerical conventions

Use refineR's actual subtraction convention x - Shift. For positive lambda, transformed support is y > -1/lambda; the normal density/CDF must be normalized on this support. At lambda = 0 use the logarithmic transform and untruncated normal. Use stable tail/log-probability calculations rather than rounding a positive tail probability to zero or clipping u to an arbitrary epsilon.

Inspection of `R/utils.R::cdfTruncatedBoxCox` found a separate negative-lambda branch and clipping of negative/invalid reported limits to zero. Before execution, document the supported fitted parameter range and reconcile the healthy CDF, truncation, and any censoring with this exact upstream implementation. A negative-lambda or censored distribution must not be silently treated as an ordinary continuous normal transform. If such fits occur in the frozen configuration, stop for a committed protocol amendment before applying the LRT to them. The validation must cover the actual supported range without changing pass-through behavior.

An anchor outside true model support gives a structural incompatibility: record p = 0 and decline, with its own reason code. Arithmetic underflow is not evidence of support violation. Degenerate transformed anchors, unavailable parameters, invalid sigma, CDF/integration failure, and unresolved rounded/censored anchor behavior are `check_failed`, not significant tests. They receive no accepted RI and are reported separately from statistical declines. Missing/invalid anchors are not replaced using routine observations. If the recovered anchor generator returns rounded measurements, specify and commit a calibrated discrete-data test before running; the continuous PIT null cannot be assumed.

### Comparators and reporting

Compare refineR alone, refineR with the anchor check, anchors-only using the recovered C2 definition and the identical 40 anchors, and the existing anchoredRI result versions. Verify paired Index/input identities and anchor hashes. Unmatched or differently generated comparisons must be labeled and excluded from paired contrasts, with their counts shown. Never rerun or modify anchoredRI in its repository.

Report separately for N <= 5,000 and N = 50,000, and within each for pathological fraction <= 20% versus > 20%. Also show individual N and scenario strata. Weight test sets equally within each primary stratum; show scenario-balanced sensitivity summaries if replicate counts differ.

Using the frozen C2 endpoint z definition, let E = max(|z_lower|, |z_upper|). Primary bad-result capture is the proportion of valid baseline fits with E > 1 that are statistically declined; repeat for E > 5. Good-result loss is the proportion with E < 0.25 that are statistically declined. Use strict inequalities; show boundary counts. Also report endpoint-level versions so an interval with one bad limit cannot be hidden by averaging.

Report statistical decline rate among evaluable checks, overall non-return rate among all planned sets, baseline fit failures, check failures, and structural incompatibilities separately. Report counts with every denominator. Failed checks do not count as successful bad-result detection. Show both the conditional capture among evaluable tests and capture among all valid baseline bad fits.

For kept results, report signed endpoint bias, mean/median |z|, capped mean |z|, E quantiles (50th, 90th, 95th, 99th), and proportions E > 1 and E > 5. The primary cap is fixed at 5: per-set loss = (min(|z_lower|,5) + min(|z_upper|,5))/2. If C2 used another cap, reproduce it as a separately labeled historical metric; do not replace the primary cap after seeing results.

Show comparator accuracy on the same kept Index set as well as on each method's full available set. The kept refineR limits must have exactly the same accuracy as ungated refineR restricted to those indices. Any apparent improvement is selection, not improved estimation. Include coverage-versus-error tables and assign loss 5 to a missing/failed/declined result in a separate all-set sensitivity summary so abstention cannot disappear from the denominator. Do not present this failure-penalized measure as accuracy of kept estimates.

Provide 95% uncertainty intervals for rates and paired loss differences, clustering by RIbench parent scenario when multiple replicates share one scenario. Freeze the grouping and interval procedure before execution after reading the benchmark schema. Use 2,000 paired cluster bootstrap resamples with seed 37000000; show raw counts and descriptive intervals without claiming population-level generalization beyond RIbench.

Stage 1 has no invented performance pass threshold. It passes technical validation only if inputs, calibration, exact preservation of kept fits, reproducibility and audits pass. Present the full usefulness results, including false declines, for user review. Stop before Stage 2 regardless of whether results look favorable.

## Stages 2–3: plans only

### Stage 2

Use anchors to select a healthy peak in `findMainPeak`, then inform starting values and search regions. Preserve the central-data healthy-only fitting approach. Focus evaluation on > 20% pathological sets. Before coding, commit the exact peak rule, parameter bounds, fallback behavior, and ablations (peak guidance, initialization, search bounds). Use development simulations separate from RIbench evaluation sets; never tune choices using benchmark truth or benchmark outcomes. Freeze one primary candidate before evaluation.

### Stage 3

Before coding, show a source-grounded derivation of `calculateCostHist` and a proposed common scale for the anchor term. The inspected code uses overlapping histogram bins, predicted counts normalized over the histogram range, a searched healthy fraction P, relaxation factor rf, selected bins within prediction bands, and multiplicative peak/tail penalties. For K selected bins, predicted counts cPred and scaled observed counts cData, its implemented cost is:

`C = -[sum(log(sqrt(P*rf/(2*pi))*sqrtCountsPred)) + K*(log(ratioCounts80)+log(ratioCounts20L)+log(ratioCounts20R)) - 0.5*sum((cData-cPred)^2/cPred)]/sqrt(K)`.

Selection, K, P, rf and penalties can vary with the candidate. This is a regularized, scaled histogram objective with dependent overlapping bins; it cannot automatically be treated as an ordinary independent-observation negative log-likelihood. Simply adding 40 anchor log densities would leave their relative weight unjustified.

The required Stage 3 proposal must specify the proper Box–Cox anchor density (including Jacobian and support normalization), the objective sign, a common reference measure/scale, how bin overlap and candidate-dependent K are handled, and the fixed weight. It must demonstrate behavior under unit changes, binning changes, and N changes. Weight zero must reproduce the preceding frozen algorithm exactly. Choose any calibration using separate simulations, not the RIbench evaluation outcomes. Show the derivation and decision rules for approval before implementation or runs.

### Fixed success criteria for each of Stages 2 and 3

Evaluate each candidate against unchanged refineR, separately at N <= 5,000 and N = 50,000. Stage 3 also reports its paired difference from Stage 2. Success requires all of the following in both sample-size groups:

- At > 20% pathological: strictly lower primary capped mean |z| than refineR.
- At <= 20% pathological: candidate minus refineR capped mean |z| <= 0.02.
- No greater count of implausible results than refineR, in either pathological-fraction stratum, using the recovered and frozen C2 definition. At minimum separately flag nonfinite/unordered limits and E > 5; clinical plausibility rules must be frozen before runs.

The cap is 5 and endpoint/test-set aggregation is defined above. For these success decisions, failures and non-returned intervals receive loss 5, all planned sets stay in the denominator, and a candidate may not reduce its implausibility count by dropping results: report failures/nonreturns separately and require their count not to increase. Report paired uncertainty intervals; the stated numerical gates use point estimates, not an undeclared significance test. A claim that all gates were met requires complete paired coverage and reproducibility audits. Failure of any gate means the stage has not met the prespecified target. Stop and show results before further work.

## Review requested now

Review this protocol before any implementation. The proposed PIT location/spread LRT and cap of 5 are explicit design choices for review. The C2 archive, anchor generator, z definition, comparator definitions, and supported CDF behavior must be resolved in committed pre-run documentation. No code, benchmark results, or claimed validation accompany this initial protocol.
