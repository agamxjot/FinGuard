
import random
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# =========================================
# 1. CONFIGURATION
# =========================================

fake = Faker("en_IN")
random.seed(42)
Faker.seed(42)

DB_PASSWORD = "4256"

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=DB_PASSWORD,
    host="localhost",
    port=5432,
    database="finguard_db"
)

engine = create_engine(db_url)

print("Starting FinGuard data generation...")

# =========================================
# 2. GENERATE EMPLOYEES
# =========================================

employees = []

designations = [
    ("Analyst", 25000),
    ("Manager", 100000),
    ("Senior Manager", 250000),
    ("Director", 1000000)
]

for i in range(1, 31):

    designation, limit = random.choice(designations)

    employees.append({
        "employee_id": f"E{i:03d}",
        "employee_name": fake.name(),
        "department": random.choice([
            "Finance", "Accounts",
            "Procurement", "Compliance"
        ]),
        "designation": designation,
        "approval_limit": limit,
        "is_active": True
    })

employees_df = pd.DataFrame(employees)

# =========================================
# 3. GENERATE VENDORS
# =========================================

vendors = []

for i in range(1, 101):

    created_date = fake.date_time_between(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2025, 6, 30)
    )

    vendors.append({
        "vendor_id": f"V{i:03d}",
        "vendor_name": fake.company(),
        "created_by": random.choice(employees)["employee_id"],
        "created_at": created_date,
        "last_payment_date": None,
        "is_active": random.choice([True, True, True, False])
    })

vendors_df = pd.DataFrame(vendors)

# =========================================
# 4. GENERATE PAYMENTS
# =========================================

payments = []

for i in range(1, 5001):

    vendor = random.choice(vendors)
    employee = random.choice(employees)

    payment_date = fake.date_time_between(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31)
    )

    amount = round(random.uniform(1000, 200000), 2)

    payments.append({
        "payment_id": f"P{i:05d}",
        "vendor_id": vendor["vendor_id"],
        "created_by": employee["employee_id"],
        "amount": amount,
        "payment_date": payment_date,
        "payment_status": random.choices(
            ["COMPLETED", "PENDING"],
            weights=[90, 10]
        )[0],
        "description": random.choice([
            "Software services",
            "Office supplies",
            "Consulting",
            "Equipment purchase",
            "Maintenance",
            "Logistics"
        ])
    })

payments_df = pd.DataFrame(payments)

# Update last payment date for each vendor
latest_dates = (
    payments_df.groupby("vendor_id")["payment_date"].max()
)

vendors_df["last_payment_date"] = (
    vendors_df["vendor_id"].map(latest_dates)
)

# =========================================
# 5. GENERATE APPROVALS
# =========================================

approvals = []

approval_number = 1

for payment in payments:

    if payment["payment_status"] == "COMPLETED":

        # Choose a different employee for normal approval
        possible_approvers = [
            e for e in employees
            if e["employee_id"] != payment["created_by"]
        ]

        approver = random.choice(possible_approvers)

        approval_date = payment["payment_date"] - timedelta(
            hours=random.randint(1, 72)
        )

        approvals.append({
            "approval_id": f"A{approval_number:06d}",
            "payment_id": payment["payment_id"],
            "approver_id": approver["employee_id"],
            "approval_level": (
                "SENIOR"
                if approver["approval_limit"] >= 250000
                else "STANDARD"
            ),
            "approval_status": "APPROVED",
            "approval_date": approval_date
        })

        approval_number += 1

approvals_df = pd.DataFrame(approvals)

# =========================================
# 6. LOAD DATA INTO POSTGRESQL
# =========================================

print("\nConnecting to PostgreSQL...")

try:

    with engine.begin() as connection:

        # Reset previous generated records
        connection.execute(text("""
            TRUNCATE TABLE
                exceptions,
                ground_truth,
                approvals,
                payments,
                vendors,
                employees
            RESTART IDENTITY CASCADE;
        """))

    employees_df.to_sql(
        "employees", engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    vendors_df.to_sql(
        "vendors", engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    payments_df.to_sql(
        "payments", engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    approvals_df.to_sql(
        "approvals", engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    print("\n========== DATA GENERATION COMPLETE ==========")

    print("Employees:", len(employees_df))
    print("Vendors:", len(vendors_df))
    print("Payments:", len(payments_df))
    print("Approvals:", len(approvals_df))

    print("\nData successfully inserted into FinGuard!")

except Exception as e:

    print("\nERROR:", e)

finally:
    engine.dispose()
