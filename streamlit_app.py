import streamlit as st
from version import VERSION, LAST_UPDATED
from datetime import datetime
import pytz

st.set_page_config(layout="wide")

# --- PAGE SETUP ---
documentation_page = st.Page(
    "views/Documentation.py",
    title="User Guild",
    icon=":material/account_circle:",
    default=True,
)
datacleaning_page = st.Page(
    "views/DataCleaning.py",
    title="Data Cleaning",
    icon=":material/account_tree:",
)
dashboard_page = st.Page(
    "views/Dashboard.py",
    title="Dashboard",
    icon=":material/smart_toy:",
)


# --- NAVIGATION SETUP ---
pg = st.navigation(
    {
        "DOCUMENTATION": [documentation_page],
        "DATA TOOLS": [datacleaning_page, dashboard_page],
    }
)


# --- LOGO SETUP ---
st.logo(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Abbott_Laboratories_logo.svg/950px-Abbott_Laboratories_logo.svg.png",
    size="large",
)


# --- SIDEBAR SETUP ---
# Convert the timestamp string to datetime object
last_updated = datetime.strptime(LAST_UPDATED, "%Y-%m-%d %H:%M:%S")


# Convert to Vietnam timezone
vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
last_updated = pytz.utc.localize(last_updated).astimezone(vietnam_tz)


# Format the timestamp
timestamp = last_updated.strftime("%d-%m-%Y %H:%M:%S")


# Add to sidebar
with st.sidebar:
    st.markdown("Made with ❤️ by Con Bo Thui")
    st.write("---")  # Add a separator line
    st.write(f"Version: {VERSION}")
    st.write(f"Last Updated: {timestamp} (GMT+7)")
    st.write("HAHA")


# --- RUN NAVIGATION ---
pg.run()
