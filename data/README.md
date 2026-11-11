# FinGuard
### Financial Governance, Risk & Internal Controls Analytics Platform

FinGuard is a financial risk intelligence platform built to
identify potential payment anomalies, monitor internal controls,
and support exception investigation.

## Key Features

- 12 SQL-based financial monitoring controls
- Duplicate payment and split transaction detection
- Approval authority and maker-checker conflict monitoring
- Vendor and employee risk scoring
- Exception investigation and audit trail
- Interactive Streamlit dashboard
- PaySim transaction analytics
- Automated QA and control validation

## Technology Stack

Python | PostgreSQL | SQL | Streamlit | Pandas | Plotly

## Dataset

- 5,000 synthetic payment transactions
- 100,000 PaySim transactions
- 240 seeded control-violation test cases
- 3,674 recorded exception entries

## Validation

- 40 automated QA checks
- 12 control presence checks
- 240/240 seeded cases detected
- Database integrity checks
- Independent SQL reconciliation

Some control-level reconciliation differences remain documented.

## How to Run

1. Clone this repository.
2. Install the dependencies:
   pip install -r requirements.txt
3. Configure your PostgreSQL credentials in a local .env file.
4. Create and populate the database using the supplied SQL scripts.
5. Run:

   streamlit run src/app.py

## Disclaimer

This project uses synthetic financial data for educational
and demonstration purposes. It is not a production banking
or fraud detection system.