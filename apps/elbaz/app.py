import streamlit as st
from databricks import sql
from databricks.sdk.core import Config
import pandas as pd

st.title("Elbaz TechDev Dashboard")

cfg = Config()

try:
    with sql.connect(
        server_hostname="adb-7405605232868969.9.azuredatabricks.net",
        http_path="/sql/1.0/warehouses/ac057f17ebf78619",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn:
        query = """
        SELECT
            SUM(CAST(AMOUNT AS DOUBLE)) AS total_spend,
            COUNT(DISTINCT Vndr_Name) AS vendor_count,
            COUNT(DISTINCT CFAS_Project) AS project_count
        FROM databricks_demo.cc950y.techdev_elbaz
        WHERE Vndr_Name IS NOT NULL
          AND CFAS_Project IS NOT NULL
          AND AMOUNT IS NOT NULL
        """
        summary = pd.read_sql(query, conn)

        st.metric("Total Spend", f"${summary['total_spend'][0]:,.0f}")
        st.metric("Vendors", f"{summary['vendor_count'][0]:,.0f}")
        st.metric("Projects", f"{summary['project_count'][0]:,.0f}")

        vendor_query = """
        SELECT
            Vndr_Name,
            SUM(CAST(AMOUNT AS DOUBLE)) AS spend
        FROM databricks_demo.cc950y.techdev_elbaz
        WHERE Vndr_Name IS NOT NULL
          AND AMOUNT IS NOT NULL
        GROUP BY Vndr_Name
        ORDER BY spend DESC
        LIMIT 20
        """
        vendor_df = pd.read_sql(vendor_query, conn)

        st.subheader("Top Vendors")
        st.bar_chart(vendor_df.set_index("Vndr_Name"))

except Exception as e:
    st.error(str(e))
