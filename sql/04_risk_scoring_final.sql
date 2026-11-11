-- ============================================================
-- FinGuard: Final Risk Scoring
-- File: 04_risk_scoring_final.sql
-- ============================================================


-- ============================================================
-- 1. Vendor Risk Scores
-- ============================================================

CREATE OR REPLACE VIEW vendor_risk_scores AS

WITH payment_risk AS (
    SELECT
        p.payment_id,
        p.vendor_id,

        COALESCE(
            MAX(
                CASE e.severity
                    WHEN 'CRITICAL' THEN 40
                    WHEN 'HIGH' THEN 25
                    WHEN 'MEDIUM' THEN 10
                    WHEN 'LOW' THEN 3
                    ELSE 0
                END
            ),
            0
        ) AS risk_points

    FROM payments p

    LEFT JOIN exceptions e
        ON p.payment_id = e.payment_id

    WHERE p.payment_status = 'COMPLETED'

    GROUP BY
        p.payment_id,
        p.vendor_id
)

SELECT
    v.vendor_id,
    v.vendor_name,

    COUNT(pr.payment_id) AS total_payments,

    COALESCE(
        SUM(pr.risk_points), 0
    ) AS total_risk_points,

    ROUND(
        100.0 * COALESCE(SUM(pr.risk_points), 0) /
        NULLIF(COUNT(pr.payment_id) * 40, 0),
        2
    ) AS risk_score,

    CASE
        WHEN 100.0 * COALESCE(SUM(pr.risk_points), 0) /
             NULLIF(COUNT(pr.payment_id) * 40, 0) >= 75
            THEN 'CRITICAL'

        WHEN 100.0 * COALESCE(SUM(pr.risk_points), 0) /
             NULLIF(COUNT(pr.payment_id) * 40, 0) >= 50
            THEN 'HIGH'

        WHEN 100.0 * COALESCE(SUM(pr.risk_points), 0) /
             NULLIF(COUNT(pr.payment_id) * 40, 0) >= 20
            THEN 'MEDIUM'

        ELSE 'LOW'
    END AS risk_category

FROM vendors v

LEFT JOIN payment_risk pr
    ON v.vendor_id = pr.vendor_id

GROUP BY
    v.vendor_id,
    v.vendor_name;


-- ============================================================
-- 2. Employee Risk Scores
-- ============================================================

CREATE OR REPLACE VIEW employee_risk_scores AS

WITH payment_risk AS (
    SELECT
        p.payment_id,
        p.created_by AS employee_id,

        COALESCE(
            MAX(
                CASE e.severity
                    WHEN 'CRITICAL' THEN 40
                    WHEN 'HIGH' THEN 25
                    WHEN 'MEDIUM' THEN 10
                    WHEN 'LOW' THEN 3
                    ELSE 0
                END
            ),
            0
        ) AS risk_points

    FROM payments p

    LEFT JOIN exceptions e
        ON p.payment_id = e.payment_id

    WHERE p.payment_status = 'COMPLETED'

    GROUP BY
        p.payment_id,
        p.created_by
)

SELECT
    emp.employee_id,
    emp.employee_name,

    COUNT(pr.payment_id) AS total_payments,

    COALESCE(
        SUM(pr.risk_points), 0
    ) AS total_risk_points,

    ROUND(
        100.0 * COALESCE(SUM(pr.risk_points), 0) /
        NULLIF(COUNT(pr.payment_id) * 40, 0),
        2
    ) AS risk_score,

    CASE
        WHEN 100.0 * COALESCE(SUM(pr.risk_points), 0) /
             NULLIF(COUNT(pr.payment_id) * 40, 0) >= 75
            THEN 'CRITICAL'

        WHEN 100.0 * COALESCE(SUM(pr.risk_points), 0) /
             NULLIF(COUNT(pr.payment_id) * 40, 0) >= 50
            THEN 'HIGH'

        WHEN 100.0 * COALESCE(SUM(pr.risk_points), 0) /
             NULLIF(COUNT(pr.payment_id) * 40, 0) >= 20
            THEN 'MEDIUM'

        ELSE 'LOW'
    END AS risk_category

FROM employees emp

LEFT JOIN payment_risk pr
    ON emp.employee_id = pr.employee_id

GROUP BY
    emp.employee_id,
    emp.employee_name;


-- ============================================================
-- END OF FINAL RISK SCORING SCRIPT
-- ============================================================