
-- =============================================
-- FINGUARD V2: NORMALIZED RISK SCORING
-- =============================================

-- VENDOR RISK SCORE
CREATE OR REPLACE VIEW vendor_risk_scores AS

WITH vendor_activity AS (
    SELECT
        v.vendor_id,
        v.vendor_name,
        COUNT(DISTINCT p.payment_id) AS total_payments
    FROM vendors v
    LEFT JOIN payments p
        ON v.vendor_id = p.vendor_id
    GROUP BY v.vendor_id, v.vendor_name
),

vendor_exceptions AS (
    SELECT
        v.vendor_id,
        COUNT(DISTINCT e.exception_id) AS exception_count,

        COUNT(DISTINCT e.exception_id)
            FILTER (WHERE e.severity = 'CRITICAL')
            AS critical_count,

        COUNT(DISTINCT e.exception_id)
            FILTER (WHERE e.severity = 'HIGH')
            AS high_count,

        COUNT(DISTINCT e.exception_id)
            FILTER (WHERE e.status = 'OPEN')
            AS open_count,

        COALESCE(SUM(
            CASE
                WHEN e.severity = 'CRITICAL' THEN 40
                WHEN e.severity = 'HIGH' THEN 25
                WHEN e.severity = 'MEDIUM' THEN 10
                WHEN e.severity = 'LOW' THEN 3
                ELSE 0
            END
        ), 0) AS weighted_points

    FROM vendors v
    LEFT JOIN payments p
        ON v.vendor_id = p.vendor_id
    LEFT JOIN exceptions e
        ON p.payment_id = e.payment_id
    GROUP BY v.vendor_id
)

SELECT
    a.vendor_id,
    a.vendor_name,
    a.total_payments,

    COALESCE(e.exception_count, 0) AS exception_count,
    COALESCE(e.critical_count, 0) AS critical_count,
    COALESCE(e.high_count, 0) AS high_count,
    COALESCE(e.open_count, 0) AS open_count,

    ROUND(
        LEAST(
            100.0,
            2.5 * COALESCE(e.weighted_points, 0)
            / GREATEST(a.total_payments, 1)
        ), 2
    ) AS risk_score,

    CASE
        WHEN 2.5 * COALESCE(e.weighted_points, 0)
             / GREATEST(a.total_payments, 1) >= 76
            THEN 'CRITICAL'
        WHEN 2.5 * COALESCE(e.weighted_points, 0)
             / GREATEST(a.total_payments, 1) >= 51
            THEN 'HIGH'
        WHEN 2.5 * COALESCE(e.weighted_points, 0)
             / GREATEST(a.total_payments, 1) >= 21
            THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_category

FROM vendor_activity a
LEFT JOIN vendor_exceptions e
    ON a.vendor_id = e.vendor_id;


-- =============================================
-- EMPLOYEE RISK SCORE
-- =============================================

CREATE OR REPLACE VIEW employee_risk_scores AS

WITH involved_payments AS (

    SELECT employee_id, payment_id
    FROM (
        SELECT
            created_by AS employee_id,
            payment_id
        FROM payments

        UNION

        SELECT
            approver_id AS employee_id,
            payment_id
        FROM approvals
    ) x
),

employee_activity AS (
    SELECT
        employee_id,
        COUNT(DISTINCT payment_id) AS total_payments
    FROM involved_payments
    GROUP BY employee_id
),

employee_exceptions AS (
    SELECT
        ip.employee_id,

        COUNT(DISTINCT e.exception_id) AS exception_count,

        COUNT(DISTINCT e.exception_id)
            FILTER (WHERE e.severity = 'CRITICAL')
            AS critical_count,

        COUNT(DISTINCT e.exception_id)
            FILTER (WHERE e.severity = 'HIGH')
            AS high_count,

        COUNT(DISTINCT e.exception_id)
            FILTER (WHERE e.status = 'OPEN')
            AS open_count,

        COALESCE(SUM(
            CASE
                WHEN e.severity = 'CRITICAL' THEN 40
                WHEN e.severity = 'HIGH' THEN 25
                WHEN e.severity = 'MEDIUM' THEN 10
                WHEN e.severity = 'LOW' THEN 3
                ELSE 0
            END
        ), 0) AS weighted_points

    FROM involved_payments ip
    JOIN exceptions e
        ON ip.payment_id = e.payment_id
    GROUP BY ip.employee_id
)

SELECT
    emp.employee_id,
    emp.employee_name,
    emp.department,
    emp.designation,

    COALESCE(a.total_payments, 0) AS total_payments,

    COALESCE(e.exception_count, 0) AS exception_count,
    COALESCE(e.critical_count, 0) AS critical_count,
    COALESCE(e.high_count, 0) AS high_count,
    COALESCE(e.open_count, 0) AS open_count,

    ROUND(
        LEAST(
            100.0,
            2.5 * COALESCE(e.weighted_points, 0)
            / GREATEST(COALESCE(a.total_payments, 0), 1)
        ), 2
    ) AS risk_score,

    CASE
        WHEN 2.5 * COALESCE(e.weighted_points, 0)
             / GREATEST(COALESCE(a.total_payments, 0), 1) >= 76
            THEN 'CRITICAL'
        WHEN 2.5 * COALESCE(e.weighted_points, 0)
             / GREATEST(COALESCE(a.total_payments, 0), 1) >= 51
            THEN 'HIGH'
        WHEN 2.5 * COALESCE(e.weighted_points, 0)
             / GREATEST(COALESCE(a.total_payments, 0), 1) >= 21
            THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_category

FROM employees emp
LEFT JOIN employee_activity a
    ON emp.employee_id = a.employee_id
LEFT JOIN employee_exceptions e
    ON emp.employee_id = e.employee_id;
