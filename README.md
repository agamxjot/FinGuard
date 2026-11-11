# FinGuard
### Financial Governance, Risk & Internal Controls Analytics Platform

FinGuard is a financial risk intelligence platform designed to identify potential payment anomalies, evaluate internal control exceptions, assess vendor and employee risk exposure, and support structured investigation workflows.

Built using Python, PostgreSQL, SQL and Streamlit, the platform combines rule-based financial monitoring with risk analytics and audit-trail capabilities.

## Key Features

- **12 Financial Controls:** SQL-based monitoring for duplicate payments, approval breaches, split transactions, maker-checker conflicts and vendor anomalies.
- **Risk Intelligence:** Vendor, employee, payment creator and approver risk profiling.
- **Exception Management:** Exception tracking, reviewer assignment, investigation notes and resolution workflows.
- **Audit Trail:** Transactional logging of exception status and reviewer changes.
- **Risk Control Matrix:** Centralized documentation of control objectives, risk descriptions, testing procedures and recommended actions.
- **Executive Dashboard:** Interactive visualizations, exception analytics and risk reporting.
- **Fraud Analytics:** PaySim transaction analysis using a dataset of 100,000 transactions.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Database | PostgreSQL |
| Query Language | SQL |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Visualization | Plotly |
| Database Connectivity | SQLAlchemy, Psycopg2 |

## Project Dataset

| Dataset | Records |
|---|---:|
| Synthetic payment transactions | 5,000 |
| Employees | 30 |
| Vendors | 100 |
| Approval records | 4,435 |
| Injected test cases | 240 |
| Recorded exception entries | 3,674 |
| PaySim transactions | 100,000 |

*All financial payment data is synthetic and intended for demonstration and testing.*

## Control Validation

- 12 financial monitoring controls implemented.
- 240/240 seeded test cases detected.
- 40 automated QA checks previously passed.
- 12/12 control presence checks previously passed.
- Database integrity checks completed.
- Independent SQL reconciliation performed across all 12 controls.

Some control-level reconciliation differences were identified and documented during validation.

## Application Modules

1. Executive Overview
2. Exception Analytics
3. Vendor Risk Intelligence
4. Employee Risk Intelligence
5. Payment Creator & Approver Risk Intelligence
6. Exception Investigation
7. Audit Trail & Change History
8. Risk Control Matrix
9. PaySim Analytics
10. Control Validation & Testing
11. Executive Risk Reporting
12. Control Performance & Exception Intelligence

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/agamxjot/FinGuard.git
cd FinGuard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure PostgreSQL

Create a PostgreSQL database named:

```text
finguard_db
```

Configure your local `.env` file with:

```env
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=finguard_db
```

Never commit your `.env` file or database credentials.

### 4. Prepare the database

Use the SQL scripts in the `sql/` directory and the data-generation and loading scripts in `scripts/` to prepare the database.

Follow the scripts' documented execution order.

### 5. Launch the application

```bash
streamlit run src/app.py
```

## Project Structure

```text
FinGuard/
├── dashboard/
├── data/
├── reports/
├── scripts/
├── sql/
├── src/
│   └── app.py
├── control_tests.py
├── qa_validation.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Disclaimer

FinGuard is an educational financial governance and risk analytics project built using synthetic data. Its risk scores and exception indicators are prioritization tools, not definitive fraud determinations or regulatory assessments. The platform is not intended for production banking use.

---

**Developed as an independent financial technology and analytics project.**