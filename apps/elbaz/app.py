import streamlit as st
from databricks import sql
from databricks.sdk.core import Config
from databricks.sdk import WorkspaceClient
import pandas as pd

st.set_page_config(
    page_title="Elbaz TechDev Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F3F4F6;
        color: #1F2937;
        font-family: "Inter", "Segoe UI", sans-serif;
    }

    .stApp > header {
        background-color: transparent;
    }

    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1440px;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0.85rem;
    }

    h1, h2, h3 {
        color: #1F2937;
        letter-spacing: -0.02em;
    }

    h1 {
        font-weight: 700;
        margin-bottom: 0.75rem;
    }

    h2, h3 {
        color: #0057B8;
        font-weight: 650;
        margin-bottom: 0.35rem;
    }

    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #D9DEE5;
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] label {
        color: #1F2937;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: #FFFFFF;
        border-color: #D9DEE5;
        border-radius: 8px;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #D9DEE5;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        box-shadow: 0 1px 3px rgba(31, 41, 55, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #6B7280;
        font-size: 0.8rem;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #0057B8;
        font-size: clamp(1.1rem, 1.5vw, 1.65rem);
        font-weight: 700;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }

    [data-testid="stMetricDelta"] {
        color: #00A8E0;
        font-size: 0.8rem;
    }

    [data-testid="stVegaLiteChart"] {
        background-color: #FFFFFF;
        border: 1px solid #D9DEE5;
        border-radius: 8px;
        padding: 0.6rem;
        box-shadow: 0 1px 3px rgba(31, 41, 55, 0.04);
    }

    [data-testid="stChatInput"] {
        border-color: #D9DEE5;
        border-radius: 8px;
    }

    hr {
        border-color: #D9DEE5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Elbaz TechDev Dashboard 🚀")

cfg = Config()
st.sidebar.header("Filters")

selected_year = st.sidebar.selectbox(
    "Year", 
    ["All", 2023, 2024, 2025, 2026]
)

selected_cash_group = st.sidebar.selectbox(
    "Cash Group", 
    [ 
        "All",
        "Fixed Bid Cash",
        "T&M Cash",
        "Other Contractor Cash"
    ]
)

selected_cost_type = st.sidebar.selectbox(
    "Cost Type",
    [
        "All",
        "Maintenance",
        "Enhancing"
    ]
)

try:
    with sql.connect(
        server_hostname="adb-7405605232868969.9.azuredatabricks.net",
        http_path="/sql/1.0/warehouses/ac057f17ebf78619",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn:

        # Dynamically pull vendor list 
        vendor_list_query = """
            SELECT DISTINCT Vndr_Name
            FROM databricks_demo.cc950y.techdev_vendor_spend
            WHERE Vndr_Name IS NOT NULL
            AND UPPER(TRIM(Vndr_Name)) <> 'NULL'
            AND TRIM(Vndr_Name) <> ''
            ORDER BY Vndr_Name
        """

        vendor_list_df = pd.read_sql(vendor_list_query, conn)
        vendor_options = ["All"] + vendor_list_df["Vndr_Name"].tolist()

        selected_vendor = st.sidebar.selectbox(
            "Vendor Name",
            vendor_options
        )

        # Build all filters
        filters = []

        if selected_year != "All":
            filters.append(f"year_num = '{selected_year}'")

        if selected_cash_group != "All":
            filters.append(
                f"Cash_Group___PRISM = '{selected_cash_group}'"
            )

        if selected_cost_type != "All":
            filters.append(
                f"COST_TYPE2 = '{selected_cost_type}'"
            )

        if selected_vendor != "All":
            safe_vendor = selected_vendor.replace("'", "''")
            filters.append(f"Vndr_Name = '{safe_vendor}'")

        where_clause = ""

        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        # Summary Metrics
        query = f"""
        SELECT
            COALESCE(SUM(TRY_CAST(AMOUNT AS DOUBLE)), 0) AS total_spend,
            COUNT(DISTINCT Vndr_Name) AS vendor_count,
            COUNT(DISTINCT CFAS_Project) AS project_count
        FROM databricks_demo.cc950y.techdev_vendor_spend
        {where_clause}
        """

        summary = pd.read_sql(query, conn)

        # Build Vendor Filter for sub-queries
        vendor_filter = where_clause

        if vendor_filter:
            vendor_filter += """
              AND Vndr_Name IS NOT NULL
              AND UPPER(TRIM(Vndr_Name)) <> 'NULL'
              AND TRIM(Vndr_Name) <> ''
            """
        else:
            vendor_filter = """
            WHERE Vndr_Name IS NOT NULL
              AND UPPER(TRIM(Vndr_Name)) <> 'NULL'
              AND TRIM(Vndr_Name) <> ''
            """

        # Largest Vendor
        largest_vendor_query = f"""
        SELECT
            Vndr_Name,
            SUM(TRY_CAST(AMOUNT AS DOUBLE)) AS spend
        FROM databricks_demo.cc950y.techdev_vendor_spend
        {vendor_filter}
        GROUP BY Vndr_Name
        ORDER BY spend DESC
        LIMIT 1
        """

        largest_vendor = pd.read_sql(largest_vendor_query, conn)

        # Executive KPI Row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Contractor Spend",
                f"${summary['total_spend'][0]:,.0f}"
            )

        with col2:
            st.metric(
                "Vendors",
                f"{summary['vendor_count'][0]:,.0f}"
            )

        with col3:
            st.metric(
                "Projects",
                f"{summary['project_count'][0]:,.0f}"
            )

        with col4:
            if not largest_vendor.empty:
                vendor_name = largest_vendor["Vndr_Name"].iloc[0]
                vendor_spend = largest_vendor["spend"].iloc[0]

                st.metric(
                    label="Largest Vendor",
                    value=vendor_name,
                    delta="${:,.0f} spend".format(vendor_spend),
                    delta_color="off"
                )
            else:
                st.metric(
                    label="Largest Vendor",
                    value="N/A"
                )

        # Vendor Chart
        vendor_query = f"""
        SELECT
            Vndr_Name,
            SUM(TRY_CAST(AMOUNT AS DOUBLE)) AS spend
        FROM databricks_demo.cc950y.techdev_vendor_spend
        {vendor_filter}
        GROUP BY Vndr_Name
        ORDER BY spend DESC
        LIMIT 20
        """

        vendor_df = pd.read_sql(vendor_query, conn)

        # Spend by Cash Group
        cash_group_query = f"""
        SELECT
            Cash_Group___PRISM AS cash_group,
            SUM(TRY_CAST(AMOUNT AS DOUBLE)) AS spend
        FROM databricks_demo.cc950y.techdev_vendor_spend
        {where_clause}
        GROUP BY Cash_Group___PRISM
        ORDER BY spend DESC
        """

        cash_group_df = pd.read_sql(cash_group_query, conn)

        #Monthly Spend Trend
        monthly_query = f"""
        SELECT
            TO_DATE(
                CONCAT(CAST(DATA_YRMO_DT AS STRING), '01'),
                'yyyyMMdd'
            ) AS month,
            SUM(TRY_CAST(AMOUNT AS DOUBLE)) AS spend
        FROM databricks_demo.cc950y.techdev_vendor_spend
        {where_clause}
        GROUP BY month
        ORDER BY month
        """

        monthly_df = pd.read_sql(monthly_query, conn)
    # Connection can close here
    
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Top Vendors")
        st.bar_chart(vendor_df.set_index("Vndr_Name"))

    with chart_col2:
        st.subheader("Spend by Cash Group")
        st.bar_chart(cash_group_df.set_index("cash_group"))

        

        st.subheader("Monthly Contractor Spend")

        st.line_chart(
            monthly_df.set_index("month")
        )
        
    # Genie Chat
    st.divider()
    st.subheader("Ask Technology Development Agent")

    w = WorkspaceClient(config=cfg)

    question = st.chat_input(
        "Ask a question about TechDev spend..."
    )

    if question:
        with st.spinner("Thinking..."):
            conversation = w.genie.start_conversation(
                space_id="01f1bb78cc7c10cc904a40bf5e06223a",
                content=question
            )

            result = conversation.result()

            for attachment in result.attachments:
                if attachment.text:
                    st.write(attachment.text.content)

except Exception as e:
    st.error(str(e))
