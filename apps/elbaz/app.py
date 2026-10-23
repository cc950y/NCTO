import streamlit as st
from databricks import sql
from databricks.sdk.core import Config
from databricks.sdk import WorkspaceClient
import pandas as pd

st.title("Elbaz TechDev Dashboard")

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
where_clause = ""

if filters:
    where_clause = "WHERE " + " AND ".join(filters)

try:
    with sql.connect(
        server_hostname="adb-7405605232868969.9.azuredatabricks.net",
        http_path="/sql/1.0/warehouses/ac057f17ebf78619",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn:

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
        #Build Vendor Filter
                # Build Vendor Filter
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
                vendor_name = largest_vendor["Vndr_Name"][0]
                vendor_spend = largest_vendor["spend"][0]

                st.metric(
                    "Largest Vendor",
                    vendor_name,
                    pend:,.0f} spend",
                    delta_color="off"
                )
            else:
                st.metric(
                    "Largest Vendor",
                    "N/A"
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

        st.subheader("Top Vendors")
        st.bar_chart(vendor_df.set_index("Vndr_Name"))

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
