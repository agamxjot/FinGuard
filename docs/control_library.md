# FinGuard — Risk Control Library

## Overview

FinGuard implements 12 SQL-based controls to identify potentially unusual payment activity, approval conflicts, vendor risks and transaction anomalies.

The controls are designed for synthetic financial data and demonstrate rule-based monitoring rather than confirmed fraud detection.

## Control Register

| Control ID | Control Name | Risk Area | Detection Objective |
|---|---|---|---|
| CTRL01 | Duplicate Payment Indicator | Duplicate payments | Identify completed payments with matching vendor, amount and payment date. |
| CTRL02 | Vendor Creator–Approver Conflict | Segregation of duties | Identify cases where the employee who created a vendor also approved payments associated with that vendor. |
| CTRL03 | Approval Authority Limit Breach | Approval governance | Identify completed approved payments exceeding the approver's configured approval limit. |
| CTRL04 | Pairwise Split Payment | Transaction splitting | Identify pairs of payments to the same vendor within 24 hours where individual amounts are below ₹1,00,000 but the combined amount exceeds ₹1,00,000. |
| CTRL05 | Weekend Payment Activity | Payment timing | Identify completed payments occurring on Saturdays or Sundays for contextual review. |
| CTRL06 | Round-Amount Payment Indicator | Transaction anomalies | Identify completed payments of at least ₹10,000 that are exact multiples of ₹10,000. |
| CTRL07 | Vendor Inactivity Gap | Vendor monitoring | Identify payments associated with a vendor whose recorded last-payment date indicates an inactivity gap of at least 365 days. |
| CTRL08 | Missing Approval | Approval compliance | Identify completed payments without a corresponding approval record. |
| CTRL09 | Late Approval | Approval timing | Identify cases where the recorded approval date is later than the payment date. |
| CTRL10 | Short-Term Vendor Payment Frequency | Vendor transaction monitoring | Identify vendors receiving at least 10 completed payments within a rolling 24-hour period. |
| CTRL11 | Payment Maker–Checker Conflict | Segregation of duties | Identify completed approved payments where the payment creator and approver are the same employee. |
| CTRL12 | Cumulative Split Payment | Transaction splitting | Identify groups of at least three same-vendor payments within 24 hours, each below ₹1,00,000, with a combined value exceeding ₹1,00,000. |

## Control Design Notes

### Segregation of Duties
CTRL02 and CTRL11 monitor different conflicts:

- CTRL02 examines the relationship between vendor creation and payment approval.
- CTRL11 examines whether the payment creator also approved the payment.

### Transaction Splitting
CTRL04 and CTRL12 examine payment patterns at different levels:

- CTRL04 identifies qualifying pairs of payments.
- CTRL12 identifies qualifying groups of three or more payments.

### Contextual Risk Indicators
CTRL05 and CTRL06 identify unusual patterns that may warrant investigation. Neither pattern alone establishes misconduct or a policy violation.

## Interpretation and Limitations

- A control detection is an exception indicator, not proof of fraud.
- Detection results depend on the quality and completeness of source data.
- Approval limits, business calendars and vendor records should reflect actual organisational policies in a production environment.
- CTRL01 cannot verify invoice-level duplication because invoice identifiers are unavailable in the synthetic dataset.
- CTRL02 and CTRL11 represent separate segregation-of-duties checks.

## Intended Use

This control library supports:

- Risk and Control Matrix documentation.
- Rule-based transaction monitoring.
- Exception investigation and prioritisation.
- Control-performance analysis.
- Audit trail and governance reporting.

