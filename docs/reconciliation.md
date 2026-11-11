# FinGuard — Control Reconciliation & Data Quality Findings

## 1. Executive Summary

FinGuard currently contains 3,674 exception records across 12 risk controls.

| Exception Origin | Records |
|---|---:|
| INJECTED_TEST | 240 |
| UNMATCHED_TO_INJECTED_TEST | 3,398 |
| NEW_CONTROL_DETECTION | 36 |
| **Total** | **3,674** |

The system detected all 240 seeded test cases. This represents 100% detection of the injected test cases, not a measurement of overall model accuracy or production fraud-detection performance.

Unmatched detections have not been independently classified as false positives or confirmed violations.

## 2. CTRL03 — Approval Authority Limit Breach

The control identifies completed, approved payments exceeding the configured approval limit of the approver.

| Designation | Approved Payments | Limit Breaches | Breach Rate |
|---|---:|---:|---:|
| Analyst | 1,016 | 908 | 89.37% |
| Manager | 907 | 450 | 49.61% |
| Senior Manager | 1,163 | 0 | 0% |
| Director | 1,349 | 0 | 0% |
| **Total** | **4,435** | **1,358** | **30.62%** |

The high detection volume is concentrated among Analysts and Managers. This indicates a potential mismatch between synthetic payment amounts and configured approval limits.

The 1,358 detections comprise 20 seeded test cases and 1,338 unmatched detections.

**Interpretation:** The control identifies approval-limit exceptions in the generated dataset. The high unmatched volume requires business-context review and should not automatically be interpreted as confirmed policy violations.

## 3. CTRL05 — Weekend Payment Activity

The control identifies completed payments occurring on Saturdays and Sundays.

| Metric | Saturday | Sunday |
|---|---:|---:|
| Total Payments | 710 | 739 |
| Completed Payments | 628 | 654 |
| Average Payment Amount | ₹1,01,141 | ₹1,02,284 |
| Total Payment Value | ₹7,18,10,256 | ₹7,55,88,111 |

There are 1,449 weekend payments, of which 1,282 were completed.

The 1,282 recorded exceptions comprise 20 seeded test cases and 1,262 unmatched detections.

**Interpretation:** Weekend activity alone does not establish suspicious behaviour or a policy breach. A production implementation should incorporate the organisation's business calendar, approved weekend operations and transaction context.

## 4. CTRL04 — Pairwise Split Payment Reconciliation

The reconstructed control logic identified seven additional payment IDs that were not represented in the recorded CTRL04 exception set.

Six additional detections overlap with CTRL01 duplicate-payment detections. One additional payment, P02263, overlaps with a CTRL12 cumulative split-payment detection.

The existing CTRL04 exception records comprise 40 seeded cases and 113 unmatched detections.

**Interpretation:** These seven additional detections require reconciliation against the original control execution and exception-generation logic. They have not been silently added to the historical exception population.

## 5. CTRL07 — Vendor Inactivity Gap Reconciliation

The reconstructed static vendor-inactivity rule reproduced 528 of the 529 recorded CTRL07 exceptions.

One historical exception was not reproduced:

- Exception ID: 3273
- Payment ID: P02906
- Vendor ID: V008
- Payment date: 2025-06-08 13:15:04
- Stored vendor last-payment date: 2024-06-08 16:46:38
- Calculated elapsed time: approximately 364.85 days

The calculated interval is below the current 365-day threshold.

**Interpretation:** The discrepancy may reflect a difference in historical rule implementation, date arithmetic or threshold handling. The original exception has been preserved pending further investigation.

## 6. Data Quality and Validation

The current QA validation suite reports:

- 40 tests executed
- 40 tests passed
- 0 failures
- 0 errors

Additional integrity checks found no duplicate payment-control exception pairs, invalid payment references, invalid control references, invalid reviewer references or audit records referencing nonexistent exceptions.

The seeded test dataset contains 240 injected cases, all of which were detected.

These results validate the tested synthetic-data scenarios and database integrity checks. They do not establish real-world fraud-detection accuracy.

## 7. Known Limitations

1. The dataset is synthetic and does not represent actual organisational payment activity.
2. CTRL01 uses vendor, amount and date matching because invoice-level identifiers are unavailable. Matches are potential duplicates, not proof of duplicate payments.
3. CTRL03 results are affected by the relationship between synthetic payment amounts and configured approval limits.
4. CTRL05 treats weekend activity as a risk indicator without an organisation-specific business calendar.
5. CTRL09 uses payment date as a timing reference; this may not represent the actual payment completion timestamp.
6. The investigation audit trail currently records the actor as SYSTEM rather than an authenticated individual user.
7. Unmatched detections have not all undergone manual investigation and should not be labelled false positives.
8. CTRL04 and CTRL07 contain documented reconciliation differences between reconstructed logic and historical exception records.

## 8. Conclusion

FinGuard demonstrates a synthetic financial-control monitoring workflow incorporating risk-control testing, exception detection, entity-level risk scoring, investigation tracking and audit logging.

The reconciliation findings distinguish seeded test coverage from unmatched detections and historical discrepancies. This supports more transparent interpretation of control results and identifies areas for further calibration before any production deployment.