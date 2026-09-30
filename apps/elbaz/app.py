import streamlit as st
from databricks import sql
from databricks.sdk.core import Config
import pandas as pd

st.title("Elbaz TechDev Dashboard")

cfg = Config()  # Automatically uses the app's service principal credentials

try:
    with sql.connect(
        server_hostname="adb-7405605232868969.9.azuredatabricks.net",
        http_path="/sql/1.0/warehouses/ac057f17ebf78619",
        credentials_provider=lambda: cfg.authenticate,
    ) as conn:
        query = """
        SELECT *
        FROM databricks_demo.cc950y.techdev_elbaz
        LIMIT 100
        """
        df = pd.read_sql(query, conn)
        st.success(f"Loaded {len(df)} rows")
        st.dataframe(df.head())

except Exception as e:
    st.error(str(e))
