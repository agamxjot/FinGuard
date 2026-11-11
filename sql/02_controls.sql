
-- =====================================================
-- FINGUARD: AUTOMATED INTERNAL CONTROL TESTING ENGINE
-- =====================================================

-- CTRL01: DUPLICATE PAYMENTS
-- Same vendor, same amount, same date

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    p.payment_id,
    'CTRL01',
    'HIGH',
    'OPEN'
FROM payments p
JOIN (
    SELECT vendor_id, amount, payment_date
    FROM payments
    WHERE payment_status = 'COMPLETED'
    GROUP BY vendor_id, amount, payment_date
    HAVING COUNT(*) > 1
) d
ON p.vendor_id = d.vendor_id
AND p.amount = d.amount
AND p.payment_date = d.payment_date
WHERE p.payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL02: SEGREGATION OF DUTIES
-- Vendor creator also approves payment

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT DISTINCT
    p.payment_id,
    'CTRL02',
    'CRITICAL',
    'OPEN'
FROM payments p
JOIN vendors v
    ON p.vendor_id = v.vendor_id
JOIN approvals a
    ON p.payment_id = a.payment_id
WHERE v.created_by = a.approver_id
AND a.approval_status = 'APPROVED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL03: APPROVAL THRESHOLD BREACH
-- Approver lacks sufficient authorization

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT DISTINCT
    p.payment_id,
    'CTRL03',
    'CRITICAL',
    'OPEN'
FROM payments p
JOIN approvals a
    ON p.payment_id = a.payment_id
JOIN employees e
    ON a.approver_id = e.employee_id
WHERE p.amount > e.approval_limit
AND a.approval_status = 'APPROVED'
AND p.payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL04: SPLIT TRANSACTIONS
-- Same vendor, multiple payments within 24 hours
-- Combined value exceeds 100,000

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT DISTINCT
    p1.payment_id,
    'CTRL04',
    'HIGH',
    'OPEN'
FROM payments p1
JOIN payments p2
    ON p1.vendor_id = p2.vendor_id
    AND p1.payment_id <> p2.payment_id
    AND p2.payment_date > p1.payment_date
    AND p2.payment_date <= p1.payment_date + INTERVAL '24 hours'
WHERE p1.amount + p2.amount > 100000
AND p1.amount < 100000
AND p2.amount < 100000
AND p1.payment_status = 'COMPLETED'
AND p2.payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL05: WEEKEND PAYMENTS

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    payment_id,
    'CTRL05',
    'MEDIUM',
    'OPEN'
FROM payments
WHERE EXTRACT(ISODOW FROM payment_date) IN (6, 7)
AND payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL06: ROUND AMOUNTS
-- Large payments in exact multiples of 10,000

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    payment_id,
    'CTRL06',
    'MEDIUM',
    'OPEN'
FROM payments
WHERE amount >= 10000
AND MOD(amount, 10000) = 0
AND payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL07: DORMANT VENDOR ACTIVITY
-- Vendor inactive for at least 365 days

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    p.payment_id,
    'CTRL07',
    'HIGH',
    'OPEN'
FROM payments p
JOIN vendors v
    ON p.vendor_id = v.vendor_id
WHERE p.payment_date::date - v.last_payment_date::date >= 365
AND p.payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL08: MISSING APPROVALS

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    p.payment_id,
    'CTRL08',
    'CRITICAL',
    'OPEN'
FROM payments p
LEFT JOIN approvals a
    ON p.payment_id = a.payment_id
WHERE a.approval_id IS NULL
AND p.payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL09: LATE APPROVALS
-- Approval recorded after payment execution

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    p.payment_id,
    'CTRL09',
    'HIGH',
    'OPEN'
FROM payments p
JOIN approvals a
    ON p.payment_id = a.payment_id
WHERE a.approval_date > p.payment_date
AND a.approval_status = 'APPROVED'
AND p.payment_status = 'COMPLETED'
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- CTRL10: UNUSUAL VENDOR CONCENTRATION
-- At least 10 payments to one vendor within 24 hours

WITH vendor_activity AS (
    SELECT
        payment_id,
        vendor_id,
        payment_date,
        COUNT(*) OVER (
            PARTITION BY vendor_id
            ORDER BY payment_date
            RANGE BETWEEN INTERVAL '24 hours' PRECEDING
            AND CURRENT ROW
        ) AS payment_count
    FROM payments
    WHERE payment_status = 'COMPLETED'
)

INSERT INTO exceptions
    (payment_id, control_id, severity, status)
SELECT
    payment_id,
    'CTRL10',
    'HIGH',
    'OPEN'
FROM vendor_activity
WHERE payment_count >= 10
ON CONFLICT (payment_id, control_id) DO NOTHING;


-- =====================================================
-- FINAL CONTROL EXECUTION SUMMARY
-- =====================================================

SELECT
    control_id,
    COUNT(*) AS exceptions_detected
FROM exceptions
GROUP BY control_id
ORDER BY control_id;
