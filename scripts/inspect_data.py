
import pandas as pd

DATA_PATH = r"C:\Users\agamj\OneDrive\Desktop\project\FinGuard\data\paysim.csv"

total_rows = 0
fraud_count = 0
legitimate_count = 0

transaction_types = {}

print("Scanning complete PaySim dataset...")

for chunk in pd.read_csv(DATA_PATH, chunksize=100000):

    total_rows += len(chunk)

    fraud_count += (chunk["isFraud"] == 1).sum()
    legitimate_count += (chunk["isFraud"] == 0).sum()

    counts = chunk["type"].value_counts()

    for transaction_type, count in counts.items():
        transaction_types[transaction_type] = (
            transaction_types.get(transaction_type, 0) + count
        )

print("\n========== COMPLETE DATASET REPORT ==========")

print("Total transactions:", total_rows)
print("Fraudulent:", fraud_count)
print("Legitimate:", legitimate_count)

print("Fraud percentage:",
      round(fraud_count / total_rows * 100, 4), "%")

print("\nTransaction types:")

for transaction_type, count in transaction_types.items():
    print(transaction_type, ":", count)

