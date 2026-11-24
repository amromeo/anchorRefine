# Stage 3 development execution record

The protocol amendment was committed at `4b82c69f821ae1e91692cd6e26151fea9fb78faf` before implementation and generation. The first source freeze was `762238a3f641a5b68796c1118c99fa19b0d9f395`.

## Influence fixture startup correction

The first influence run stopped at its zero-weight identity assertion. On the same frozen fixture, scoring a single Stage 2 fit twice produced identical native and historical endpoints, signed errors, PIT statistics, p-values and release decisions. The historical extractor also recorded RIbench’s first-load message about registering its S3 print method. The second call had no registration message. The exact comparison includes the captured conditions. [Original run 45407381211](https://github.com/amromeo/anchorRefine/actions/runs/45407381211)

Load both namespaces at process startup, in refineR then RIbench order. The workflow logs the registration message once per R session. Keep the exact comparison of all score fields and conditions, original fixtures and seeds, weights and methods. Preserve the original Actions artifacts and logs. At this correction full development and confirmation were unopened, and no aggregated influence results were available. Repeat the full fixture audit before development.

## Amendment for Stage 2 fallback datasets

The completed original influence check showed that Stage 2 had used its fallback in 17 of 24 fixtures at N = 1,000 and 13 of 24 at N = 1,500. Under the original rule the primary arm returned those fits for every weight. The post-fit comparator could update them. [Original influence check](../results/stage3-influence-45407973511/REPORT.md)

Development under that rule started and was cancelled at the investigator's request. Twenty fit jobs had started. Some individual cases completed, but the jobs stopped before writing shard-level fit tables. The original logs, artifacts and counts are retained. A separate local one-case technical replay used the original source. The interrupted run and the local replay supply no observations for weight selection. [Cancelled development run](https://github.com/amromeo/anchorRefine/actions/runs/45409118727)

Commit `57f305a101c9696ec329b784f93c1b0dc74d0151` records the investigator's amendment before implementation or an amended run. For a valid Stage 2 fallback parent, a positive weight now uses the original unguided refineR histogram and search regions. Weight zero returns the Stage 2 parent directly. The rerun uses the same frozen fixtures and development cases. It reports all fixtures and the subsets defined by the original Stage 2 fallback status. Only complete amended development results may supply the weights.
