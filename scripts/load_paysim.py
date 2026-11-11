
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os

# ==========================================
# 1. DATABASE CONFIGURATION
# ==========================================

DB_PASSWORD = "PASSWORD"

db_url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password=DB_PASSWORD,
    host="localhost",
    port=5432,
    database="finguard_db"
)

engine = create_engine(db_url)

# ==========================================
# 2. DATASET PATH
# ==========================================

DATA_PATH = (
    r"C:\Users\agamj\OneDrive\Desktop"
    r"\project\FinGuard\data\paysim.csv"
)

# ==========================================
# 3. CHECK FILE
# ==========================================

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"PaySim dataset not found: {DATA_PATH}"
    )

try:

    print("Reading PaySim dataset...")

    # Load first 100,000 records
    df = pd.read_csv(
        DATA_PATH,
        nrows=100000
    )

    print("Rows loaded:", len(df))

    # ==========================================
    # 4. RENAME COLUMNS
    # ==========================================

    df = df.rename(columns={
        "type": "transaction_type",
        "nameOrig": "sender_id",
        "oldbalanceOrg": "old_balance_origin",
        "newbalanceOrig": "new_balance_origin",
        "nameDest": "receiver_id",
        "oldbalanceDest": "old_balance_destination",
        "newbalanceDest": "new_balance_destination",
        "isFraud": "is_fraud",
        "isFlaggedFraud": "is_flagged_fraud"
    })

    print("\nColumns mapped successfully.")

    # ==========================================
    # 5. VALIDATE COLUMNS
    # ==========================================

    required_columns = [
        "step",
        "transaction_type",
        "amount",
        "sender_id",
        "old_balance_origin",
        "new_balance_origin",
        "receiver_id",
        "old_balance_destination",
        "new_balance_destination",
        "is_fraud",
        "is_flagged_fraud"
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    df = df[required_columns]

    # ==========================================
    # 6. DATA TYPE CONVERSION
    # ==========================================

    df["is_fraud"] = df["is_fraud"].astype(bool)

    df["is_flagged_fraud"] = (
        df["is_flagged_fraud"].astype(bool)
    )

    df["amount"] = pd.to_numeric(
        df["amount"], errors="raise"
    )

    print("Data validation successful.")

    # ==========================================
    # 7. CLEAR PREVIOUS IMPORT
    # ==========================================

    print("\nClearing previous PaySim records...")

    with engine.begin() as connection:

        connection.execute(text("""
            TRUNCATE TABLE paysim_transactions
            RESTART IDENTITY;
        """))

    # ==========================================
    # 8. INSERT INTO POSTGRESQL
    # ==========================================

    print("\nImporting PaySim into PostgreSQL...")

    df.to_sql(
        name="paysim_transactions",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=1000
    )

    print("\nPaySim import completed!")

    # ==========================================
    # 9. DATABASE VERIFICATION
    # ==========================================

    print("\n========== DATABASE VERIFICATION ==========")

    with engine.connect() as connection:

        result = connection.execute(text("""
            SELECT
                COUNT(*) AS total_transactions,

                COUNT(*) FILTER (
                    WHERE is_fraud = TRUE
                ) AS fraud_count,

                COUNT(*) FILTER (
                    WHERE is_fraud = FALSE
                ) AS legitimate_count,

                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE is_fraud = TRUE
                    ) / NULLIF(COUNT(*), 0),
                    4
                ) AS fraud_percentage

            FROM paysim_transactions;
        """))

        row = result.fetchone()

        print("Total transactions:", row[0])
        print("Fraudulent transactions:", row[1])
        print("Legitimate transactions:", row[2])
        print("Fraud percentage:", row[3], "%")

        print("\nFirst five database records:")

        sample = pd.read_sql(
            "SELECT * FROM paysim_transactions LIMIT 5",
            connection
        )

        print(sample)

    print("\nSUCCESS: FinGuard PaySim database populated!")

except Exception as error:

    print("\nIMPORT FAILED:")
    print(repr(error))

finally:

    engine.dispose()

