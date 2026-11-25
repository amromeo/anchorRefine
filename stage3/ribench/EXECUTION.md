# Stage 3 RIbench execution record

The investigator approved the sampled audit and both fixed arms. Commit `453821a3505560fe6a43311e757708d030c8bc97` records the protocol. Commit `c2cc6f4fbf55814afe4cf7bbba41e0640edf6ce0` records the 432 audit indices. The first execution freeze was `c47ebd1090ffcfc3622f779c86f4ce4bbe798304`.

## Nominal and observed sample size

During the first small-cohort run, a local replay of three prespecified audit cases matched the archived unchanged refineR and Stage 2 fits and checks. The verification code for the Task G export then compared the length of the observed routine vector to nominal RIbench N. Hb Index 64 contains 999 observations and AST Index 1744 contains 998, although both belong to the N = 1,000 design stratum. CRP Index 4672 contains 1,000. The archived design already records the nominal N and the observed length (`routine_n`) for every Index.

The first hosted attempt was cancelled before a cohort report was available. Preserve its available artifacts and logs. Correct the export check to require exact equality to `routine_n` and retain both `N` and `routine_n` in the dataset index. The original vectors, hashes, weights, fit code, sample assignments, comparison groups and tolerances remain those in the preregistered protocol. This was a file-verification error. No sampled same-host or separate-host fit discrepancy had been observed. Repeat the small cohort from the corrected source freeze before opening the large cohort. [First small-cohort attempt](https://github.com/amromeo/anchorRefine/actions/runs/45529627972)
