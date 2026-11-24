# Reproduction of the selected Stage 2 rule on development

All **1,440/1,440** development datasets reproduced the archived K = 24 peak-only fit under the frozen comparison rules. The selected entry point refit the routine measurements from their original seeds using the original 40 guidance anchors. Each fit was checked on the guidance and fresh panels with both PIT seeds, giving 5,760 check records. The audit compared the initial election, search branches, fallback, model parameters, both limit extractions, signed endpoint errors, check probabilities and releases.

| Routine N | Pathology | Datasets | Native pre-check mean loss | Native checked mean loss | Guidance declines | Fallbacks |
|---:|---|---:|---:|---:|---:|---:|
| 1,500 | >20% | 432 | 0.6233 | 1.4878 | 111 | 187 |
| 1,500 | ≤20% | 288 | 0.2109 | 0.5121 | 19 | 119 |
| 50,000 | >20% | 432 | 0.2227 | 0.6789 | 44 | 21 |
| 50,000 | ≤20% | 288 | 0.0768 | 0.1784 | 6 | 4 |

The table uses all assigned datasets. Loss averages two absolute endpoint errors, each capped at 5. A failed fit or, after checking, a withheld interval contributes 5. The release uses the primary guidance-panel PIT seed.

The exact archive comparisons matched 1,440 fit hashes and the four check records on 1,440 datasets. All 48 same-machine shard repeats matched byte for byte. The 48 independent machine comparisons had a maximum endpoint difference of 0 times interval width and a maximum absolute p-value difference of 0. The development audit recorded 0 discrepancies outside tolerance. The successful reproduction qualifies the frozen rule for the prespecified independent confirmation run.

On datasets 16 and 19, RIbench printed its one-time method-registration message while the selected fit was being scored. In the original multi-arm job, the same message appeared while scoring the baseline. The fitted objects, endpoints, signed scores, p-values and decisions matched exactly on both cases.

[Selection and reason](../../PROTOCOL.md#stage-2-candidate-decision-after-the-development-ablations) · [Decision data](../../stage2/selected-decision.csv) · [Case comparisons](evidence/matches.csv.gz) · [Audit](evidence/audit.json) · [Eligibility receipt](eligibility.json) · [Source freeze](https://github.com/amromeo/anchorRefine/commit/c043917226b20929296b80cda53e0ae293968b42) · [Actions run](https://github.com/amromeo/anchorRefine/actions/runs/45299765250)
