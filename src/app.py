
import os
import streamlit as st
import pandas as pd
import plotly.express as px

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, URL

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="FinGuard | Risk Intelligence",
    page_icon="🛡️",
    layout="wide"
)

load_dotenv()

# ==========================================
# 2. DATABASE CONNECTION
# ==========================================

@st.cache_resource
def get_engine():

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "finguard_db")
    )

    return create_engine(url, pool_pre_ping=True)


engine = get_engine()


@st.cache_data(ttl=30)
def fetch_data(query):
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection)


# ==========================================
# 3. HEADER
# ==========================================

st.title("🛡️ FINGUARD")
st.subheader("Financial Governance & Internal Control Intelligence")

st.caption(
    "Automated control testing | Fraud analytics | "
    "Vendor risk | Employee risk | Exception management"
)

st.divider()


# ==========================================
# 4. LOAD DATABASE DATA
# ==========================================

try:
    vendor_df = fetch_data("""
        SELECT * FROM vendor_risk_scores
        ORDER BY risk_score DESC
    """)

    employee_df = fetch_data("""
        SELECT * FROM employee_risk_scores
        ORDER BY risk_score DESC
    """)
    
    creator_df = fetch_data("""
        SELECT *
        FROM employee_creator_risk_scores
        ORDER BY risk_score DESC
    """)

    approver_df = fetch_data("""
        SELECT *
        FROM employee_approver_risk_scores
        ORDER BY risk_score DESC
    """)


    exception_df = fetch_data("""
        SELECT
            exception_id,
            payment_id,
            control_id,
            severity,
            status,
            reviewer_id,
            detected_at,
            exception_origin,
            investigation_notes,
            resolution_remarks,
            resolved_at
        FROM exceptions
        ORDER BY exception_id DESC
    """)

    control_df = fetch_data("""
        SELECT control_id, severity,
               COUNT(*) AS exception_count
        FROM exceptions
        GROUP BY control_id, severity
    """)
    validation_df = fetch_data("""
        WITH injected AS (
            SELECT
                control_id,
                COUNT(*) AS injected_cases
            FROM ground_truth
            WHERE is_injected = TRUE
            GROUP BY control_id
        ),
        detected AS (
            SELECT
                control_id,
                COUNT(*) FILTER (
                    WHERE exception_origin = 'INJECTED_TEST'
                ) AS detected_cases,
                COUNT(*) FILTER (
                    WHERE exception_origin = 'UNMATCHED_TO_INJECTED_TEST'
                ) AS unmatched_detections
            FROM exceptions
            GROUP BY control_id
        )
        SELECT
            i.control_id,
            i.injected_cases,
            COALESCE(d.detected_cases, 0) AS detected_cases,
            i.injected_cases - COALESCE(d.detected_cases, 0)
                AS missed_cases,
            COALESCE(d.unmatched_detections, 0)
                AS unmatched_detections,
            ROUND(
                100.0 * COALESCE(d.detected_cases, 0)
                / NULLIF(i.injected_cases, 0),
                2
            ) AS detection_rate
        FROM injected i
        LEFT JOIN detected d
            ON i.control_id = d.control_id
        ORDER BY i.control_id
    """)

    summary_df = fetch_data("""
        SELECT
            COUNT(*) AS total_exceptions,
            COUNT(*) FILTER (WHERE status = 'OPEN')
                AS open_exceptions,
            COUNT(*) FILTER (WHERE status = 'UNDER REVIEW')
                AS under_review,
            COUNT(*) FILTER (WHERE status = 'CONFIRMED')
                AS confirmed,
            COUNT(*) FILTER (WHERE severity = 'CRITICAL')
                AS critical
        FROM exceptions
    """)

    
    paysim_df = fetch_data("""
        SELECT
            COUNT(*) AS total_transactions,
            COUNT(*) FILTER (WHERE is_fraud = TRUE)
                AS fraud_transactions,
            COALESCE(SUM(amount), 0) AS transaction_value
        FROM paysim_transactions
    """)
    
    control_performance_df = fetch_data("""
        SELECT *
        FROM control_performance_analytics
        ORDER BY total_exceptions DESC
    """)



except Exception as error:
    st.error(f"Database loading failed: {error}")
    st.stop()

# Verify all datasets loaded
st.success("All database tables and views loaded successfully!")

print("PaySim loaded:", paysim_df.shape)
print(paysim_df.head())

# ==========================================
# 5. SIDEBAR FILTERS
# ==========================================

st.sidebar.title("Dashboard Controls")

severity_options = sorted(
    exception_df["severity"].dropna().unique()
)

selected_severity = st.sidebar.multiselect(
    "Filter by severity",
    severity_options,
    default=severity_options
)

status_options = sorted(
    exception_df["status"].dropna().unique()
)

selected_status = st.sidebar.multiselect(
    "Filter by status",
    status_options,
    default=status_options
)

filtered_exceptions = exception_df[
    exception_df["severity"].isin(selected_severity)
    & exception_df["status"].isin(selected_status)
]

if st.sidebar.button("Refresh dashboard"):
    st.cache_data.clear()
    st.rerun()


# ==========================================
# 6. EXECUTIVE OVERVIEW
# ==========================================

st.header("Executive Overview")

s = summary_df.iloc[0]
p = paysim_df.iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "PaySim Transactions",
    f"{int(p.total_transactions):,}"
)

col2.metric(
    "Total Exceptions",
    f"{int(s.total_exceptions):,}"
)

col3.metric(
    "Critical Exceptions",
    f"{int(s.critical):,}"
)

col4.metric(
    "Open Exceptions",
    f"{int(s.open_exceptions):,}"
)

col5.metric(
    "PaySim Fraud",
    f"{int(p.fraud_transactions):,}"
)

st.divider()


# ==========================================
# 7. EXCEPTION ANALYTICS
# ==========================================

st.header("Exception Analytics")

left, right = st.columns(2)

with left:

    st.subheader("Exceptions by Control")

    control_chart = (
        filtered_exceptions.groupby("control_id")
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        control_chart,
        x="control_id",
        y="count",
        color="count",
        title="Control-wise Exception Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)


with right:

    st.subheader("Severity Distribution")

    severity_chart = (
        filtered_exceptions.groupby("severity")
        .size()
        .reset_index(name="count")
    )

    fig = px.pie(
        severity_chart,
        names="severity",
        values="count",
        hole=0.45,
        title="Exception Severity"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 8. VENDOR RISK
# ==========================================

st.divider()

st.header("Vendor Risk Intelligence")

left, right = st.columns([1.3, 1])

with left:

    st.subheader("Top 10 High-Risk Vendors")

    fig = px.bar(
        vendor_df.head(10).sort_values("risk_score"),
        x="risk_score",
        y="vendor_name",
        orientation="h",
        color="risk_category",
        title="Vendor Risk Ranking"
    )

    st.plotly_chart(fig, use_container_width=True)


with right:

    st.subheader("Vendor Risk Distribution")

    vendor_distribution = (
        vendor_df.groupby("risk_category")
        .size()
        .reset_index(name="count")
    )

    fig = px.pie(
        vendor_distribution,
        names="risk_category",
        values="count",
        hole=0.45
    )

    st.plotly_chart(fig, use_container_width=True)


st.dataframe(
    vendor_df,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 9. EMPLOYEE RISK
# ==========================================

st.divider()

st.header("Employee Risk Intelligence")

left, right = st.columns(2)

with left:

    st.subheader("Highest Risk Employees")

    fig = px.bar(
        employee_df.head(10).sort_values("risk_score"),
        x="risk_score",
        y="employee_name",
        orientation="h",
        color="risk_category"
    )

    st.plotly_chart(fig, use_container_width=True)


with right:

    st.subheader("Employee Risk Distribution")

    employee_distribution = (
        employee_df.groupby("risk_category")
        .size()
        .reset_index(name="count")
    )

    fig = px.pie(
        employee_distribution,
        names="risk_category",
        values="count",
        hole=0.45
    )

    st.plotly_chart(fig, use_container_width=True)


st.dataframe(
    employee_df,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# EMPLOYEE CREATOR RISK INTELLIGENCE
# ==========================================

st.divider()
st.header("Employee Creator Risk Intelligence")

st.caption(
    "Risk exposure associated with employees who create payments. "
    "This measures payment-related exposure, not individual culpability."
)

if not creator_df.empty:

    col1, col2, col3 = st.columns(3)

    col1.metric("Employees Analysed", len(creator_df))

    col2.metric(
        "High-Risk Creators",
        int(creator_df["risk_category"].isin(
            ["HIGH", "CRITICAL"]
        ).sum())
    )

    col3.metric(
        "Average Risk Score",
        f"{creator_df['risk_score'].mean():.2f}"
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Payment Creators by Risk")

        fig = px.bar(
            creator_df.head(10).sort_values("risk_score"),
            x="risk_score",
            y="employee_name",
            orientation="h",
            color="risk_category",
            title="Creator Risk Ranking"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Creator Risk Distribution")

        creator_distribution = (
            creator_df.groupby("risk_category")
            .size()
            .reset_index(name="count")
        )

        fig = px.pie(
            creator_distribution,
            names="risk_category",
            values="count",
            hole=0.45
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Creator Risk Register")

    st.dataframe(
        creator_df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No creator risk records available.")


# ==========================================
# EMPLOYEE APPROVER RISK INTELLIGENCE
# ==========================================

st.divider()
st.header("Employee Approver Risk Intelligence")

st.caption(
    "Risk exposure associated with employees approving payments. "
    "Approval-limit breaches and other control exceptions contribute "
    "to the exposure score. This is not a measure of culpability."
)

if not approver_df.empty:

    col1, col2, col3 = st.columns(3)

    col1.metric("Employees Analysed", len(approver_df))

    col2.metric(
        "High-Risk Approvers",
        int(approver_df["risk_category"].isin(
            ["HIGH", "CRITICAL"]
        ).sum())
    )

    col3.metric(
        "Average Risk Score",
        f"{approver_df['risk_score'].mean():.2f}"
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Payment Approvers by Risk")

        fig = px.bar(
            approver_df.head(10).sort_values("risk_score"),
            x="risk_score",
            y="employee_name",
            orientation="h",
            color="risk_category",
            title="Approver Risk Ranking"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Approver Risk Distribution")

        approver_distribution = (
            approver_df.groupby("risk_category")
            .size()
            .reset_index(name="count")
        )

        fig = px.pie(
            approver_distribution,
            names="risk_category",
            values="count",
            hole=0.45
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Approver Risk Register")

    st.dataframe(
        approver_df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No approver risk records available.")


# ==========================================
# CREATOR VS APPROVER COMPARISON
# ==========================================

st.divider()
st.header("Creator vs Approver Risk Comparison")

st.caption(
    "Comparison of employee-associated risk exposure "
    "across payment creation and approval responsibilities."
)

comparison_df = pd.concat([
    creator_df.assign(role="Payment Creator"),
    approver_df.assign(role="Payment Approver")
], ignore_index=True)

fig = px.bar(
    comparison_df,
    x="employee_name",
    y="risk_score",
    color="role",
    barmode="group",
    title="Employee Risk Score: Creator vs Approver"
)

fig.update_layout(
    xaxis_title="Employee",
    yaxis_title="Risk Score",
    xaxis_tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

comparison_summary = comparison_df.pivot(
    index="employee_name",
    columns="role",
    values="risk_score"
).reset_index()

comparison_summary["Approver Minus Creator"] = (
    comparison_summary["Payment Approver"]
    - comparison_summary["Payment Creator"]
)

st.subheader("Role-wise Risk Score Comparison")

st.dataframe(
    comparison_summary.sort_values(
        "Approver Minus Creator",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

# ==========================================
# 10. EXCEPTION INVESTIGATION WORKFLOW
# ==========================================

st.divider()

st.header("Exception Investigation")

st.caption(
    "Search, assign, investigate and resolve control exceptions."
)

# Load available employees for reviewer assignment
reviewers_df = fetch_data("""
    SELECT employee_id, employee_name, designation
    FROM employees
    ORDER BY employee_name
""")

reviewer_map = {
    f"{row.employee_name} ({row.employee_id})": row.employee_id
    for row in reviewers_df.itertuples()
}

# Search filters
col1, col2, col3 = st.columns(3)

with col1:
    search_payment = st.text_input("Search Payment ID")

with col2:
    control_options = ["ALL"] + sorted(
        exception_df["control_id"].dropna().unique().tolist()
    )
    selected_control = st.selectbox(
        "Control",
        control_options
    )

with col3:
    workflow_statuses = ["ALL"] + sorted(
        exception_df["status"].dropna().unique().tolist()
    )
    selected_workflow_status = st.selectbox(
        "Investigation Status",
        workflow_statuses
    )

# Apply filters
investigation_df = exception_df.copy()

if search_payment.strip():
    investigation_df = investigation_df[
        investigation_df["payment_id"].astype(str).str.contains(
            search_payment.strip(),
            case=False,
            na=False
        )
    ]

if selected_control != "ALL":
    investigation_df = investigation_df[
        investigation_df["control_id"] == selected_control
    ]

if selected_workflow_status != "ALL":
    investigation_df = investigation_df[
        investigation_df["status"] == selected_workflow_status
    ]

st.subheader("Exception Register")

st.dataframe(
    investigation_df,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("Update an Exception")

if investigation_df.empty:
    st.warning("No exceptions match the selected filters.")

else:
    selected_exception = st.selectbox(
        "Select Exception ID",
        investigation_df["exception_id"].tolist()
    )

    current_exception = investigation_df[
        investigation_df["exception_id"] == selected_exception
    ].iloc[0]

    st.write(
        f"**Payment:** {current_exception['payment_id']}  |  "
        f"**Control:** {current_exception['control_id']}  |  "
        f"**Severity:** {current_exception['severity']}"
    )

    st.write(
        f"**Current status:** {current_exception['status']}"
    )

    current_reviewer = current_exception["reviewer_id"]

    reviewer_options = ["Unassigned"] + list(reviewer_map.keys())

    default_reviewer = "Unassigned"

    for label, employee_id in reviewer_map.items():
        if employee_id == current_reviewer:
            default_reviewer = label
            break

    with st.form("exception_investigation_form"):

        selected_reviewer_label = st.selectbox(
            "Assign Reviewer",
            reviewer_options,
            index=reviewer_options.index(default_reviewer)
        )

        new_status = st.selectbox(
            "Update Status",
            ["OPEN", "UNDER REVIEW", "CONFIRMED", "FALSE POSITIVE"]
        )

        investigation_notes = st.text_area(
            "Investigation Notes",
            value=(
                current_exception["investigation_notes"]
                if pd.notna(current_exception["investigation_notes"])
                else ""
            ),
            placeholder="Describe the investigation and evidence..."
        )

        resolution_remarks = st.text_area(
            "Resolution Remarks",
            value=(
                current_exception["resolution_remarks"]
                if pd.notna(current_exception["resolution_remarks"])
                else ""
            ),
            placeholder="Enter the reason for the final decision..."
        )

        submit_update = st.form_submit_button(
            "Save Investigation Update"
        )

        if submit_update:

            reviewer_id = reviewer_map.get(
                selected_reviewer_label
            )

            if new_status in ["CONFIRMED", "FALSE POSITIVE"] \
                    and not resolution_remarks.strip():
                st.error(
                    "Please enter resolution remarks before closing an exception."
                )

            else:
                
                try:
                    with engine.begin() as connection:
    
                        # Get existing values before updating
                        old_record = connection.execute(
                            text("""
                                SELECT status, reviewer_id
                                FROM exceptions
                                WHERE exception_id = :exception_id
                                FOR UPDATE
                            """),
                            {"exception_id": int(selected_exception)}
                        ).mappings().first()
    
                        if old_record is None:
                            raise ValueError("Exception record not found.")
    
                        old_status = old_record["status"]
                        old_reviewer = old_record["reviewer_id"]
    
                        # Update exception record
                        connection.execute(
                            text("""
                                UPDATE exceptions
                                SET
                                    reviewer_id = :reviewer_id,
                                    status = :status,
                                    investigation_notes = :notes,
                                    resolution_remarks = :remarks,
                                    resolved_at = CASE
                                        WHEN :status IN (
                                            'CONFIRMED',
                                            'FALSE POSITIVE'
                                        )
                                        THEN CURRENT_TIMESTAMP
                                        ELSE NULL
                                    END
                                WHERE exception_id = :exception_id
                            """),
                            {
                                "reviewer_id": reviewer_id,
                                "status": new_status,
                                "notes": investigation_notes,
                                "remarks": resolution_remarks,
                                "exception_id": int(selected_exception)
                            }
                        )
    
                        # Record the change in audit log
                        connection.execute(
                            text("""
                                INSERT INTO exception_audit_log (
                                    exception_id,
                                    action,
                                    old_status,
                                    new_status,
                                    old_reviewer_id,
                                    new_reviewer_id,
                                    changed_by,
                                    remarks
                                )
                                VALUES (
                                    :exception_id,
                                    'INVESTIGATION_UPDATE',
                                    :old_status,
                                    :new_status,
                                    :old_reviewer,
                                    :new_reviewer,
                                    'SYSTEM',
                                    :remarks
                                )
                            """),
                            {
                                "exception_id": int(selected_exception),
                                "old_status": old_status,
                                "new_status": new_status,
                                "old_reviewer": old_reviewer,
                                "new_reviewer": reviewer_id,
                                "remarks": resolution_remarks or investigation_notes
                            }
                        )
    
                    st.cache_data.clear()
                    st.success("Investigation and audit log saved successfully!")
                    st.rerun()
    
                except Exception as error:
                    st.error(f"Could not save update: {error}")

# ==========================================
# 11. AUDIT TRAIL
# ==========================================

st.divider()

st.header("Audit Trail & Change History")

st.caption(
    "Track historical changes to exception status, "
    "reviewer assignments and investigation remarks."
)

audit_df = fetch_data("""
    SELECT
        audit_id,
        exception_id,
        action,
        old_status,
        new_status,
        old_reviewer_id,
        new_reviewer_id,
        changed_by,
        change_timestamp,
        remarks
    FROM exception_audit_log
    ORDER BY change_timestamp DESC
""")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Audit Events", len(audit_df))

with col2:
    st.metric(
        "Exceptions with Audit Records",
        audit_df["exception_id"].nunique()
        if not audit_df.empty else 0
    )

if not audit_df.empty:

    st.subheader("Recent Changes")

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Exception History")

    selected_audit_exception = st.selectbox(
        "Select Exception ID for History",
        sorted(
            audit_df["exception_id"].unique(),
            reverse=True
        )
    )

    history_df = audit_df[
        audit_df["exception_id"] == selected_audit_exception
    ].sort_values("change_timestamp")

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No audit events recorded yet.")

# ==========================================
# 12. RISK CONTROL MATRIX
# ==========================================

st.divider()

st.header("Risk Control Matrix (RCM)")

st.caption(
    "Central register of financial risks, control objectives, "
    "testing procedures and remediation recommendations."
)

rcm_df = fetch_data("""
    SELECT
        r.control_id,
        r.control_name,
        r.risk_description,
        r.control_objective,
        r.testing_procedure,
        r.control_frequency,
        r.risk_level,
        r.recommended_action,
        COUNT(e.exception_id) AS exception_count
    FROM risk_control_matrix r
    LEFT JOIN exceptions e
        ON r.control_id = e.control_id
    GROUP BY
        r.control_id,
        r.control_name,
        r.risk_description,
        r.control_objective,
        r.testing_procedure,
        r.control_frequency,
        r.risk_level,
        r.recommended_action
    ORDER BY r.control_id
""")

# RCM summary metrics

col1, col2, col3 = st.columns(3)

col1.metric("Total Controls", len(rcm_df))

col2.metric(
    "Critical Risk Controls",
    int((rcm_df["risk_level"] == "CRITICAL").sum())
)

col3.metric(
    "Exceptions Across Controls",
    int(rcm_df["exception_count"].sum())
)

# Search and filter

col1, col2 = st.columns(2)

with col1:
    selected_risk = st.selectbox(
        "Filter by Risk Level",
        ["ALL"] + sorted(rcm_df["risk_level"].unique())
    )

with col2:
    search_control = st.text_input(
        "Search Control",
        placeholder="Enter control name or ID"
    )

filtered_rcm = rcm_df.copy()

if selected_risk != "ALL":
    filtered_rcm = filtered_rcm[
        filtered_rcm["risk_level"] == selected_risk
    ]

if search_control.strip():
    search_mask = (
        filtered_rcm["control_name"].str.contains(
            search_control, case=False, na=False
        )
        |
        filtered_rcm["control_id"].str.contains(
            search_control, case=False, na=False
        )
    )
    filtered_rcm = filtered_rcm[search_mask]

st.subheader("Control Register")

st.dataframe(
    filtered_rcm[
        [
            "control_id",
            "control_name",
            "risk_level",
            "control_frequency",
            "exception_count"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

# Detailed control information

st.subheader("Control Details")

if not filtered_rcm.empty:

    selected_control_id = st.selectbox(
        "Select Control",
        filtered_rcm["control_id"].tolist(),
        key="rcm_control_details"
    )

    control = filtered_rcm[
        filtered_rcm["control_id"] == selected_control_id
    ].iloc[0]

    st.markdown(f"### {control['control_name']}")

    st.write("**Risk Level:**", control["risk_level"])
    st.write("**Frequency:**", control["control_frequency"])

    st.write("**Risk Description**")
    st.write(control["risk_description"])

    st.write("**Control Objective**")
    st.write(control["control_objective"])

    st.write("**Testing Procedure**")
    st.write(control["testing_procedure"])

    st.write("**Recommended Action**")
    st.info(control["recommended_action"])

else:
    st.info("No controls match your filters.")


# ==========================================
# CONTROL PERFORMANCE INTELLIGENCE
# ==========================================

st.divider()

st.header("Control Performance & Exception Intelligence")

st.caption(
    "SQL-driven analysis of control-level exception volumes, "
    "severity distribution, injected-case detection and workflow status."
)

# KPI metrics

total_controls = len(control_performance_df)

total_exceptions = int(
    control_performance_df["total_exceptions"].sum()
)

injected_cases = int(
    control_performance_df["injected_cases"].sum()
)

unmatched = int(
    control_performance_df["unmatched_detections"].sum()
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Financial Controls", f"{total_controls:,}")
col2.metric("Total Exceptions", f"{total_exceptions:,}")
col3.metric("Injected Cases", f"{injected_cases:,}")
col4.metric("Unmatched Detections", f"{unmatched:,}")

st.divider()

# Control-wise exception chart

st.subheader("Control-wise Exception Distribution")

fig = px.bar(
    control_performance_df,
    x="control_id",
    y="total_exceptions",
    color="risk_level",
    hover_data=[
        "control_name",
        "critical_exceptions",
        "high_exceptions",
        "open_exceptions"
    ],
    title="Exception Volume by Financial Control"
)

st.plotly_chart(fig, use_container_width=True)

# Severity distribution

st.subheader("Control Severity Intelligence")

severity_data = control_performance_df[
    [
        "critical_exceptions",
        "high_exceptions",
        "medium_exceptions",
        "low_exceptions"
    ]
].sum().reset_index()

severity_data.columns = ["Severity", "Count"]

severity_data["Severity"] = (
    severity_data["Severity"]
    .str.replace("_exceptions", "", regex=False)
    .str.upper()
)

fig = px.pie(
    severity_data,
    names="Severity",
    values="Count",
    hole=0.45,
    title="Overall Exception Severity Distribution"
)

st.plotly_chart(fig, use_container_width=True)

# Control performance table

st.subheader("Control Performance Scorecard")

display_columns = [
    "control_id",
    "control_name",
    "risk_level",
    "injected_cases",
    "matched_injected",
    "unmatched_detections",
    "total_exceptions",
    "critical_exceptions",
    "high_exceptions",
    "open_exceptions",
    "confirmed_exceptions",
    "injected_case_detection_rate"
]

st.dataframe(
    control_performance_df[display_columns],
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Injected-case detection rate is calculated only where "
    "injected ground-truth cases exist. Unmatched detections "
    "are not automatically classified as false positives."
)


# ==========================================
# 11. PAYSIM FRAUD ANALYTICS
# ==========================================

st.divider()

st.header("PaySim Fraud Analytics")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Transactions",
    f"{int(p.total_transactions):,}"
)

col2.metric(
    "Fraudulent Transactions",
    f"{int(p.fraud_transactions):,}"
)

fraud_rate = (
    100 * p.fraud_transactions / p.total_transactions
    if p.total_transactions else 0
)

col3.metric(
    "Fraud Rate",
    f"{fraud_rate:.4f}%"
)



# ==========================================
# 12. CONTROL VALIDATION & TESTING
# ==========================================

st.divider()

st.header("Control Validation & Testing")

st.caption(
    "Validation against deliberately injected test cases. "
    "Unmatched detections are not automatically false positives."
)

# Overall validation metrics

total_injected = int(validation_df["injected_cases"].sum())
total_detected = int(validation_df["detected_cases"].sum())
total_missed = int(validation_df["missed_cases"].sum())
total_unmatched = int(validation_df["unmatched_detections"].sum())

overall_detection_rate = (
    100 * total_detected / total_injected
    if total_injected else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Injected Test Cases",
    f"{total_injected:,}"
)

col2.metric(
    "Detected Test Cases",
    f"{total_detected:,}"
)

col3.metric(
    "Missed Test Cases",
    f"{total_missed:,}"
)

col4.metric(
    "Detection Rate",
    f"{overall_detection_rate:.2f}%"
)

# Control-wise detection chart

st.subheader("Control-wise Detection Performance")

fig = px.bar(
    validation_df,
    x="control_id",
    y="detection_rate",
    text="detection_rate",
    range_y=[0, 110],
    title="Injected Test Detection Rate by Control"
)

fig.update_traces(
    marker_color="#36A2EB",
    texttemplate="%{text:.1f}%",
    textposition="outside"
)

fig.update_layout(
    yaxis_title="Detection Rate (%)",
    xaxis_title="Control ID",
    showlegend=False
)

fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# Detailed validation table

st.subheader("Control-wise Validation Results")

st.dataframe(
    validation_df,
    use_container_width=True,
    hide_index=True
)

# Classification of all detected exceptions

st.subheader("Exception Classification")

classification_df = fetch_data("""
    SELECT
        exception_origin,
        COUNT(*) AS exception_count
    FROM exceptions
    GROUP BY exception_origin
    ORDER BY exception_origin
""")

fig = px.pie(
    classification_df,
    names="exception_origin",
    values="exception_count",
    hole=0.45,
    title="Injected Tests vs Unmatched Rule Detections"
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    f"{total_unmatched:,} exceptions were detected by the rules "
    "but do not match the injected test reference. "
    "They require independent investigation and should not "
    "automatically be treated as false positives."
)


# ==========================================
# 14. EXECUTIVE RISK INTELLIGENCE REPORT
# ==========================================

st.divider()

st.header("Executive Risk Intelligence Report")

st.caption(
    "Consolidated overview of financial control exceptions, "
    "entity risk exposure and validation performance."
)

# ------------------------------------------
# Executive KPIs
# ------------------------------------------

total_exceptions = int(s.total_exceptions)
critical_exceptions = int(s.critical)
open_exceptions = int(s.open_exceptions)

high_exceptions = int(
    exception_df["severity"].eq("HIGH").sum()
)

injected_detected = int(
    exception_df["exception_origin"]
    .eq("INJECTED_TEST").sum()
)

unmatched_detections = int(
    exception_df["exception_origin"]
    .eq("UNMATCHED_TO_INJECTED_TEST").sum()
)

vendor_high = int(
    vendor_df["risk_category"].eq("HIGH").sum()
)

employee_high = int(
    employee_df["risk_category"].eq("HIGH").sum()
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Exceptions", f"{total_exceptions:,}")
col2.metric("Critical Exceptions", f"{critical_exceptions:,}")
col3.metric("High Exceptions", f"{high_exceptions:,}")
col4.metric("Open Exceptions", f"{open_exceptions:,}")

col1, col2, col3, col4 = st.columns(4)

col1.metric("High-Risk Vendors", vendor_high)
col2.metric("High-Risk Employees", employee_high)
col3.metric("Injected Tests Detected", f"{injected_detected:,}")
col4.metric("Unmatched Detections", f"{unmatched_detections:,}")

# ------------------------------------------
# Risk distribution
# ------------------------------------------

st.subheader("Entity Risk Distribution")

left, right = st.columns(2)

with left:
    vendor_dist = (
        vendor_df.groupby("risk_category")
        .size()
        .reset_index(name="count")
    )

    fig = px.pie(
        vendor_dist,
        names="risk_category",
        values="count",
        hole=0.5,
        title="Vendor Risk Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

with right:
    employee_dist = (
        employee_df.groupby("risk_category")
        .size()
        .reset_index(name="count")
    )

    fig = px.pie(
        employee_dist,
        names="risk_category",
        values="count",
        hole=0.5,
        title="Employee Risk Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# Top risk entities
# ------------------------------------------

st.subheader("Priority Risk Entities")

left, right = st.columns(2)

with left:
    st.markdown("**Top 5 High-Risk Vendors**")

    st.dataframe(
        vendor_df.sort_values(
            "risk_score", ascending=False
        ).head(5),
        use_container_width=True,
        hide_index=True
    )

with right:
    st.markdown("**Top 5 High-Risk Employees**")

    st.dataframe(
        employee_df.sort_values(
            "risk_score", ascending=False
        ).head(5),
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------
# Key observations
# ------------------------------------------

st.subheader("Executive Observations")

st.warning(
    f"{critical_exceptions:,} exceptions are classified as CRITICAL. "
    "These should receive priority investigation."
)

st.info(
    f"{injected_detected:,} of "
    f"{injected_detected + int(validation_df['missed_cases'].sum()):,} "
    f"deliberately injected test cases were detected. "
    f"Detection rate: {overall_detection_rate:.2f}%."
)

st.warning(
    f"{unmatched_detections:,} detections do not match the injected "
    "test reference. They are not automatically false positives "
    "and require independent review."
)

# ------------------------------------------
# Recommended actions
# ------------------------------------------

st.subheader("Recommended Management Actions")

recommendations = [
    "Prioritize investigation of critical and high-severity exceptions.",
    "Review CTRL03 approval-limit breaches and strengthen maker-checker controls.",
    "Review the 12 high-risk vendors and 8 high-risk employees.",
    "Investigate unmatched rule detections before classifying them.",
    "Maintain reviewer assignments, resolution remarks and audit history."
]

for item in recommendations:
    st.markdown(f"- {item}")

# ------------------------------------------
# Downloadable reports
# ------------------------------------------

st.subheader("Download Executive Data")

report_df = exception_df.merge(
    rcm_df[["control_id", "control_name", "risk_level"]],
    on="control_id",
    how="left"
)

csv_data = report_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Exception Report (CSV)",
    data=csv_data,
    file_name="finguard_exception_report.csv",
    mime="text/csv"
)

vendor_csv = vendor_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Vendor Risk Report (CSV)",
    data=vendor_csv,
    file_name="finguard_vendor_risk_report.csv",
    mime="text/csv"
)

employee_csv = employee_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Employee Risk Report (CSV)",
    data=employee_csv,
    file_name="finguard_employee_risk_report.csv",
    mime="text/csv"
)

# ==========================================
# 13. FOOTER
# ==========================================

st.divider()

st.caption(
    "FinGuard | Financial Governance & Internal "
    "Control Intelligence | Academic Portfolio Project"
)
