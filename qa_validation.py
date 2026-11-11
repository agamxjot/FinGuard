
import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

# ==========================================
# FINGUARD - AUTOMATED QA VALIDATION ENGINE
# ==========================================

load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "finguard_db")
)

engine = create_engine(url, pool_pre_ping=True)

results = []

def run_test(name, query, condition, description):
    try:
        with engine.connect() as conn:
            value = conn.execute(text(query)).scalar()

        passed = condition(value)

        results.append({
            "Test": name,
            "Result": "PASS" if passed else "FAIL",
            "Value": str(value),
            "Description": description
        })

    except Exception as error:
        results.append({
            "Test": name,
            "Result": "ERROR",
            "Value": str(error),
            "Description": description
        })


print("\n======================================")
print("       FINGUARD QA VALIDATION")
print("======================================\n")

# 1. Database connectivity
run_test(
    "Database Connectivity",
    "SELECT 1",
    lambda x: x == 1,
    "PostgreSQL connection is operational"
)

# 2. Core table inventory
tables = [
    "payments",
    "vendors",
    "employees",
    "approvals",
    "exceptions",
    "ground_truth",
    "risk_control_matrix",
    "exception_audit_log",
    "duplicate_payment_evidence",
    "paysim_transactions"
]

for table in tables:
    run_test(
        f"Table: {table}",
        f"SELECT to_regclass('public.{table}') IS NOT NULL",
        lambda x: x is True,
        f"Checks existence of {table}"
    )

# 3. Payment volume
run_test(
    "Payment Records",
    "SELECT COUNT(*) FROM payments",
    lambda x: x > 0,
    "Payment dataset is populated"
)

# 4. Vendor volume
run_test(
    "Vendor Records",
    "SELECT COUNT(*) FROM vendors",
    lambda x: x > 0,
    "Vendor master is populated"
)

# 5. Employee volume
run_test(
    "Employee Records",
    "SELECT COUNT(*) FROM employees",
    lambda x: x > 0,
    "Employee master is populated"
)

# 6. Approval volume
run_test(
    "Approval Records",
    "SELECT COUNT(*) FROM approvals",
    lambda x: x > 0,
    "Approval records are populated"
)

# 7. Control register
run_test(
    "Control Register",
    "SELECT COUNT(*) FROM risk_control_matrix",
    lambda x: x == 12,
    "Expected 12 financial controls"
)


# 8. Exception origin reconciliation
run_test(
    "Exception Origin Reconciliation",
    """
    WITH total AS (
        SELECT COUNT(*) AS n
        FROM exceptions
    ),
    categorized AS (
        SELECT COUNT(*) AS n
        FROM exceptions
        WHERE exception_origin IN (
            'INJECTED_TEST',
            'UNMATCHED_TO_INJECTED_TEST',
            'NEW_CONTROL_DETECTION'
        )
    )
    SELECT total.n = categorized.n
    FROM total, categorized
    """,
    lambda x: x is True,
    "Every exception has a recognized origin"
)

# 9. Exception status reconciliation
run_test(
    "Exception Status Reconciliation",
    """
    WITH total AS (
        SELECT COUNT(*) AS n FROM exceptions
    ),
    categorized AS (
        SELECT COUNT(*) AS n
        FROM exceptions
        WHERE status IN (
            'OPEN',
            'UNDER REVIEW',
            'CONFIRMED',
            'FALSE POSITIVE'
        )
    )
    SELECT total.n = categorized.n
    FROM total, categorized
    """,
    lambda x: x is True,
    "Every exception has a recognized workflow status"
)

# 10. Payment-to-vendor integrity
run_test(
    "Payment Vendor Integrity",
    """
    SELECT COUNT(*)
    FROM payments p
    LEFT JOIN vendors v
        ON p.vendor_id = v.vendor_id
    WHERE v.vendor_id IS NULL
    """,
    lambda x: x == 0,
    "Every payment references an existing vendor"
)

# 11. Payment creator integrity
run_test(
    "Payment Creator Integrity",
    """
    SELECT COUNT(*)
    FROM payments p
    LEFT JOIN employees e
        ON p.created_by = e.employee_id
    WHERE e.employee_id IS NULL
    """,
    lambda x: x == 0,
    "Every payment creator exists in employee master"
)

# 12. Approval payment integrity
run_test(
    "Approval Payment Integrity",
    """
    SELECT COUNT(*)
    FROM approvals a
    LEFT JOIN payments p
        ON a.payment_id = p.payment_id
    WHERE p.payment_id IS NULL
    """,
    lambda x: x == 0,
    "Every approval references an existing payment"
)

# 13. Approval employee integrity
run_test(
    "Approval Employee Integrity",
    """
    SELECT COUNT(*)
    FROM approvals a
    LEFT JOIN employees e
        ON a.approver_id = e.employee_id
    WHERE e.employee_id IS NULL
    """,
    lambda x: x == 0,
    "Every approver exists in employee master"
)

# 14. Vendor creator integrity
run_test(
    "Vendor Creator Integrity",
    """
    SELECT COUNT(*)
    FROM vendors v
    LEFT JOIN employees e
        ON v.created_by = e.employee_id
    WHERE v.created_by IS NOT NULL
      AND e.employee_id IS NULL
    """,
    lambda x: x == 0,
    "Vendor creators reference valid employees"
)

# 15. Ground truth payment integrity
run_test(
    "Ground Truth Payment Integrity",
    """
    SELECT COUNT(*)
    FROM ground_truth g
    LEFT JOIN payments p
        ON g.payment_id = p.payment_id
    WHERE p.payment_id IS NULL
    """,
    lambda x: x == 0,
    "Every ground-truth record references a payment"
)

# 16. Audit log integrity
run_test(
    "Audit Log Referential Integrity",
    """
    SELECT COUNT(*)
    FROM exception_audit_log a
    LEFT JOIN exceptions e
        ON a.exception_id = e.exception_id
    WHERE e.exception_id IS NULL
    """,
    lambda x: x == 0,
    "Every audit record references an exception"
)

# 17. Duplicate evidence integrity
run_test(
    "Duplicate Evidence Integrity",
    """
    SELECT COUNT(*)
    FROM duplicate_payment_evidence d
    LEFT JOIN payments p1
        ON d.payment_id = p1.payment_id
    LEFT JOIN payments p2
        ON d.matching_payment_id = p2.payment_id
    WHERE p1.payment_id IS NULL
       OR p2.payment_id IS NULL
    """,
    lambda x: x == 0,
    "Both payment references exist in duplicate evidence"
)


# 9. No duplicate payment/control combinations
run_test(
    "Duplicate Exception Check",
    """
    SELECT COUNT(*)
    FROM (
        SELECT payment_id, control_id
        FROM exceptions
        GROUP BY payment_id, control_id
        HAVING COUNT(*) > 1
    ) d
    """,
    lambda x: x == 0,
    "No duplicate payment/control exception pairs"
)

# 10. Invalid control references
run_test(
    "RCM Referential Integrity",
    """
    SELECT COUNT(*)
    FROM exceptions e
    LEFT JOIN risk_control_matrix r
        ON e.control_id = r.control_id
    WHERE r.control_id IS NULL
    """,
    lambda x: x == 0,
    "Every exception control exists in the RCM"
)

# 11. Invalid payment references
run_test(
    "Payment Referential Integrity",
    """
    SELECT COUNT(*)
    FROM exceptions e
    LEFT JOIN payments p
        ON e.payment_id = p.payment_id
    WHERE p.payment_id IS NULL
    """,
    lambda x: x == 0,
    "Every exception references a valid payment"
)

# 12. Invalid employee references
run_test(
    "Reviewer Referential Integrity",
    """
    SELECT COUNT(*)
    FROM exceptions e
    LEFT JOIN employees emp
        ON e.reviewer_id = emp.employee_id
    WHERE e.reviewer_id IS NOT NULL
      AND emp.employee_id IS NULL
    """,
    lambda x: x == 0,
    "Assigned reviewers exist in employee master"
)

# 13. Injected ground truth detection
run_test(
    "Injected Case Detection",
    """
    SELECT COUNT(*)
    FROM ground_truth g
    WHERE g.is_injected = TRUE
      AND NOT EXISTS (
          SELECT 1
          FROM exceptions e
          WHERE e.payment_id = g.payment_id
            AND e.control_id = g.control_id
            AND e.exception_origin = 'INJECTED_TEST'
      )
    """,
    lambda x: x == 0,
    "No injected ground-truth case is missing"
)

# 14. Risk views
views = [
    "vendor_risk_scores",
    "employee_risk_scores",
    "employee_creator_risk_scores",
    "employee_approver_risk_scores"
]

for view in views:
    run_test(
        f"Risk View: {view}",
        f"SELECT COUNT(*) FROM {view}",
        lambda x: x > 0,
        f"Checks that {view} returns records"
    )

# 15. Risk score range
for view in views:
    run_test(
        f"Risk Score Range: {view}",
        f"""
        SELECT COUNT(*)
        FROM {view}
        WHERE risk_score IS NULL
           OR risk_score < 0
           OR risk_score > 100
        """,
        lambda x: x == 0,
        "Risk scores must remain between 0 and 100"
    )

# 16. PaySim dataset
run_test(
    "PaySim Dataset",
    "SELECT COUNT(*) FROM paysim_transactions",
    lambda x: x > 0,
    "PaySim transaction dataset is populated"
)

# ==========================================
# DISPLAY RESULTS
# ==========================================

df = pd.DataFrame(results)

print(df.to_string(index=False))

passed = (df["Result"] == "PASS").sum()
failed = (df["Result"] == "FAIL").sum()
errors = (df["Result"] == "ERROR").sum()
total = len(df)

print("\n======================================")
print("             QA SUMMARY")
print("======================================")
print(f"Total Tests : {total}")
print(f"Passed      : {passed}")
print(f"Failed      : {failed}")
print(f"Errors      : {errors}")

if failed == 0 and errors == 0:
    print("\nSYSTEM VALIDATION: ALL TESTS PASSED")
else:
    print("\nSYSTEM VALIDATION: REVIEW REQUIRED")

df.to_csv("qa_validation_report.csv", index=False)

print("\nReport saved: qa_validation_report.csv")

engine.dispose()
