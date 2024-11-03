import streamlit as st

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


# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {
        "Documentation": [documentation_page],
        "Data Tools": [datacleaning_page, dashboard_page],
    }
)


# --- SHARED ON ALL PAGES ---
st.logo(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Abbott_Laboratories_logo.svg/950px-Abbott_Laboratories_logo.svg.png",
    size="large",
)
st.sidebar.markdown("Made with ❤️ by Con Bo Thui")


# --- RUN NAVIGATION ---
pg.run()
