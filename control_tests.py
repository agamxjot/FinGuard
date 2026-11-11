
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

load_dotenv()

url = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "finguard_db")
)

engine = create_engine(url, pool_pre_ping=True)

# Independent, read-only checks against the existing dataset.
tests = [
    ("CTRL01", "Duplicate payment evidence exists",
     """SELECT COUNT(*) FROM duplicate_payment_evidence""",
     lambda x: x > 0),

    ("CTRL02", "Vendor creator/approver conflict detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL02'""",
     lambda x: x > 0),

    ("CTRL03", "Approval threshold breach detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL03'""",
     lambda x: x > 0),

    ("CTRL04", "Pairwise split payment detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL04'""",
     lambda x: x > 0),

    ("CTRL05", "Weekend payment detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL05'""",
     lambda x: x > 0),

    ("CTRL06", "Round amount detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL06'""",
     lambda x: x > 0),

    ("CTRL07", "Vendor inactivity detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL07'""",
     lambda x: x > 0),

    ("CTRL08", "Missing approval detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL08'""",
     lambda x: x > 0),

    ("CTRL09", "Late approval detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL09'""",
     lambda x: x > 0),

    ("CTRL10", "Short-term vendor frequency detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL10'""",
     lambda x: x > 0),

    ("CTRL11", "Payment maker-checker detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL11'""",
     lambda x: x > 0),

    ("CTRL12", "Cumulative split payment detections",
     """SELECT COUNT(*) FROM exceptions WHERE control_id='CTRL12'""",
     lambda x: x > 0),
]

results = []

print("\nFINGUARD CONTROL TESTING FRAMEWORK")
print("=" * 65)

with engine.connect() as conn:
    for control_id, description, query, condition in tests:
        try:
            count = conn.execute(text(query)).scalar()
            passed = condition(count)

            results.append({
                "Control": control_id,
                "Test": description,
                "Detection Count": count,
                "Result": "PASS" if passed else "FAIL"
            })

        except Exception as error:
            results.append({
                "Control": control_id,
                "Test": description,
                "Detection Count": str(error),
                "Result": "ERROR"
            })

df = pd.DataFrame(results)

print(df.to_string(index=False))

print("\n" + "=" * 65)
print("CONTROL TEST SUMMARY")
print("=" * 65)
print("Controls tested:", len(df))
print("Passed:", (df["Result"] == "PASS").sum())
print("Failed:", (df["Result"] == "FAIL").sum())
print("Errors:", (df["Result"] == "ERROR").sum())

df.to_csv("control_test_report.csv", index=False)

print("\nReport saved: control_test_report.csv")

engine.dispose()
