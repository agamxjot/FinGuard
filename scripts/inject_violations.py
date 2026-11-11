
import random
from datetime import timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ==================================================
# 1. CONFIGURATION
# ==================================================

random.seed(42)

DB_PASSWORD = "YOUR_PASSWORD"

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=DB_PASSWORD,
    host="localhost",
    port=5432,
    database="finguard_db"
)

engine = create_engine(db_url)

CONTROL_COUNTS = 20

# ==================================================
# 2. HELPER FUNCTIONS
# ==================================================

def record_ground_truth(conn, payment_ids, control_id, violation):
    """Record every affected payment in ground truth."""

    for payment_id in payment_ids:
        conn.execute(text("""
            INSERT INTO ground_truth
                (payment_id, control_id, violation_type, is_injected)
            VALUES
                (:pid, :cid, :violation, TRUE)
            ON CONFLICT (payment_id, control_id) DO NOTHING
        """), {
            "pid": payment_id,
            "cid": control_id,
            "violation": violation
        })


def update_payment_date(conn, payment_id, new_date):
    conn.execute(text("""
        UPDATE payments
        SET payment_date = :new_date
        WHERE payment_id = :pid
    """), {"new_date": new_date, "pid": payment_id})


# ==================================================
# 3. MAIN INJECTION PROCESS
# ==================================================

try:

    print("Starting FinGuard violation injection...")

    with engine.begin() as conn:

        # Prevent accidental repeated injection
        existing = conn.execute(text("""
            SELECT COUNT(*) FROM ground_truth
            WHERE is_injected = TRUE
        """)).scalar()

        if existing > 0:
            raise RuntimeError(
                "Ground truth already contains injected records. "
                "Restore backups before running again."
            )

        # Get 240 unique completed payments
        payments = conn.execute(text("""
            SELECT payment_id, vendor_id, created_by, amount,
                   payment_date
            FROM payments
            WHERE payment_status = 'COMPLETED'
            ORDER BY random()
            LIMIT 240
        """)).mappings().all()

        if len(payments) < 240:
            raise RuntimeError("Not enough completed payments.")

        # Get employees and their authority limits
        employees = conn.execute(text("""
            SELECT employee_id, approval_limit
            FROM employees
            WHERE is_active = TRUE
        """)).mappings().all()

        # Get vendors
        vendors = conn.execute(text("""
            SELECT vendor_id, created_by
            FROM vendors
        """)).mappings().all()

        employee_map = {
            e["employee_id"]: e["approval_limit"]
            for e in employees
        }

        # Split into independent groups
        groups = {}
        cursor = 0

        groups["duplicate"] = payments[cursor:cursor+40]
        cursor += 40

        groups["sod"] = payments[cursor:cursor+20]
        cursor += 20

        groups["threshold"] = payments[cursor:cursor+20]
        cursor += 20

        groups["split"] = payments[cursor:cursor+40]
        cursor += 40

        groups["weekend"] = payments[cursor:cursor+20]
        cursor += 20

        groups["round"] = payments[cursor:cursor+20]
        cursor += 20

        groups["dormant"] = payments[cursor:cursor+20]
        cursor += 20

        groups["missing"] = payments[cursor:cursor+20]
        cursor += 20

        groups["late"] = payments[cursor:cursor+20]
        cursor += 20

        groups["concentration"] = payments[cursor:cursor+20]

        # ------------------------------------------
        # CTRL01: DUPLICATE PAYMENTS
        # ------------------------------------------

        print("Injecting CTRL01...")

        duplicate_records = groups["duplicate"]

        for i in range(0, 40, 2):

            original = duplicate_records[i]
            duplicate = duplicate_records[i+1]

            conn.execute(text("""
                UPDATE payments
                SET vendor_id = :vendor,
                    amount = :amount,
                    payment_date = :payment_date
                WHERE payment_id = :pid
            """), {
                "vendor": original["vendor_id"],
                "amount": original["amount"],
                "payment_date": original["payment_date"],
                "pid": duplicate["payment_id"]
            })

            record_ground_truth(
                conn,
                [original["payment_id"], duplicate["payment_id"]],
                "CTRL01",
                "Duplicate payment"
            )

        # ------------------------------------------
        # CTRL02: SEGREGATION OF DUTIES
        # Vendor creator also approves payment
        # ------------------------------------------

        print("Injecting CTRL02...")

        for p in groups["sod"]:

            vendor_creator = conn.execute(text("""
                SELECT created_by
                FROM vendors
                WHERE vendor_id = :vid
            """), {"vid": p["vendor_id"]}).scalar()

            if vendor_creator:

                conn.execute(text("""
                    UPDATE approvals
                    SET approver_id = :approver
                    WHERE payment_id = :pid
                """), {
                    "approver": vendor_creator,
                    "pid": p["payment_id"]
                })

                record_ground_truth(
                    conn, [p["payment_id"]],
                    "CTRL02",
                    "Segregation of duties violation"
                )

        # ------------------------------------------
        # CTRL03: APPROVAL THRESHOLD BREACH
        # ------------------------------------------

        print("Injecting CTRL03...")

        junior_employees = [
            e["employee_id"]
            for e in employees
            if e["approval_limit"] <= 100000
        ]

        if not junior_employees:
            raise RuntimeError("No eligible junior approvers found.")

        for p in groups["threshold"]:

            junior = random.choice(junior_employees)

            conn.execute(text("""
                UPDATE payments
                SET amount = 300000
                WHERE payment_id = :pid
            """), {"pid": p["payment_id"]})

            conn.execute(text("""
                UPDATE approvals
                SET approver_id = :approver,
                    approval_level = 'STANDARD'
                WHERE payment_id = :pid
            """), {
                "approver": junior,
                "pid": p["payment_id"]
            })

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL03",
                "Insufficient approval authority"
            )

        # ------------------------------------------
        # CTRL04: SPLIT TRANSACTIONS
        # Two payments just below 100,000
        # Same vendor, same date
        # ------------------------------------------

        print("Injecting CTRL04...")

        split_records = groups["split"]

        for i in range(0, 40, 2):

            first = split_records[i]
            second = split_records[i+1]

            conn.execute(text("""
                UPDATE payments
                SET vendor_id = :vendor,
                    amount = 95000,
                    payment_date = :date
                WHERE payment_id = :pid
            """), {
                "vendor": first["vendor_id"],
                "date": first["payment_date"],
                "pid": first["payment_id"]
            })

            conn.execute(text("""
                UPDATE payments
                SET vendor_id = :vendor,
                    amount = 94000,
                    payment_date = :date
                WHERE payment_id = :pid
            """), {
                "vendor": first["vendor_id"],
                "date": first["payment_date"] + timedelta(hours=1),
                "pid": second["payment_id"]
            })

            record_ground_truth(
                conn,
                [first["payment_id"], second["payment_id"]],
                "CTRL04",
                "Potential split transaction"
            )

        # ------------------------------------------
        # CTRL05: WEEKEND PAYMENTS
        # ------------------------------------------

        print("Injecting CTRL05...")

        for p in groups["weekend"]:

            date = p["payment_date"]

            # Move date to the next Sunday
            days_ahead = (6 - date.weekday()) % 7
            days_ahead = days_ahead if days_ahead else 7

            weekend_date = (
                date + timedelta(days=days_ahead)
            )

            update_payment_date(
                conn, p["payment_id"], weekend_date
            )

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL05",
                "Weekend transaction"
            )

        # ------------------------------------------
        # CTRL06: ROUND AMOUNTS
        # ------------------------------------------

        print("Injecting CTRL06...")

        for p in groups["round"]:

            amount = random.choice([
                10000, 20000, 50000,
                100000, 150000, 200000
            ])

            conn.execute(text("""
                UPDATE payments
                SET amount = :amount
                WHERE payment_id = :pid
            """), {
                "amount": amount,
                "pid": p["payment_id"]
            })

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL06",
                "Unusual round amount"
            )

        # ------------------------------------------
        # CTRL07: DORMANT VENDOR REACTIVATION
        # ------------------------------------------

        print("Injecting CTRL07...")

        for p in groups["dormant"]:

            old_date = p["payment_date"] - timedelta(days=400)

            conn.execute(text("""
                UPDATE vendors
                SET last_payment_date = :old_date
                WHERE vendor_id = :vid
            """), {
                "old_date": old_date,
                "vid": p["vendor_id"]
            })

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL07",
                "Dormant vendor activity"
            )

        # ------------------------------------------
        # CTRL08: MISSING APPROVALS
        # ------------------------------------------

        print("Injecting CTRL08...")

        for p in groups["missing"]:

            conn.execute(text("""
                DELETE FROM approvals
                WHERE payment_id = :pid
            """), {"pid": p["payment_id"]})

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL08",
                "Missing approval"
            )

        # ------------------------------------------
        # CTRL09: LATE APPROVALS
        # ------------------------------------------

        print("Injecting CTRL09...")

        for p in groups["late"]:

            late_date = p["payment_date"] + timedelta(days=2)

            conn.execute(text("""
                UPDATE approvals
                SET approval_date = :late_date
                WHERE payment_id = :pid
            """), {
                "late_date": late_date,
                "pid": p["payment_id"]
            })

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL09",
                "Late approval"
            )

        # ------------------------------------------
        # CTRL10: VENDOR PAYMENT CONCENTRATION
        # 20 payments to one vendor within a day
        # ------------------------------------------

        print("Injecting CTRL10...")

        concentration_records = groups["concentration"]

        concentration_vendor = concentration_records[0]["vendor_id"]

        concentration_date = concentration_records[0]["payment_date"]

        for p in concentration_records:

            conn.execute(text("""
                UPDATE payments
                SET vendor_id = :vendor,
                    payment_date = :date
                WHERE payment_id = :pid
            """), {
                "vendor": concentration_vendor,
                "date": concentration_date,
                "pid": p["payment_id"]
            })

            record_ground_truth(
                conn, [p["payment_id"]],
                "CTRL10",
                "Unusual vendor payment concentration"
            )

    print("\n======================================")
    print("FINGUARD VIOLATION INJECTION COMPLETE")
    print("======================================")

    print("CTRL01 - Duplicate payments: 40 records")
    print("CTRL02 - Segregation of duties: 20")
    print("CTRL03 - Threshold breach: 20")
    print("CTRL04 - Split transactions: 40")
    print("CTRL05 - Weekend payments: 20")
    print("CTRL06 - Round amounts: 20")
    print("CTRL07 - Dormant vendors: 20")
    print("CTRL08 - Missing approvals: 20")
    print("CTRL09 - Late approvals: 20")
    print("CTRL10 - Vendor concentration: 20")

    print("\nTotal affected payment records: 240")

except Exception as e:

    print("\nINJECTION FAILED:")
    print(repr(e))

finally:
    engine.dispose()
