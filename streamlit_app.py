import streamlit as st
from version import VERSION, LAST_UPDATED
from datetime import datetime
import pytz

# Extra utilities
from streamlit_extras.add_vertical_space import add_vertical_space

st.set_page_config(layout="wide")


# --- FUNCTION SETUP ---
# Hàm hiển thị thông tin trong sidebar
def display_version_info(updates):
    with st.sidebar:
        st.write("**Update Notes:**")

        # Hiển thị các updates dưới dạng bullet points
        for update in updates:
            st.markdown(f"• {update}")


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
calculation_page = st.Page(
    "views/SmartCalculation.py",
    title="Smart Calculator",
    icon=":material/smart_toy:",
)


# --- NAVIGATION SETUP ---
pg = st.navigation(
    {
        "DOCUMENTATION": [documentation_page],
        "DATA TOOLS": [datacleaning_page, dashboard_page],
        "CALCULATION": [calculation_page]
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
    st.write(f"**Version:** {VERSION}")
    st.write(f"**Last Updated:** {timestamp}")

    # List chứa các update mới
    updates = [
        "Chỉnh sửa tính năng trích xuất brand & format",
        "Thêm cột Voucher"
    ]
    display_version_info(updates=updates)

    add_vertical_space(1)

    st.markdown(
        """
        <style>
        @keyframes border-dance {
            0% {
                background-position: left top, right top, right bottom, left bottom;
            }
            25% {
                background-position: right top, right bottom, left bottom, left top;
            }
            50% {
                background-position: right bottom, left bottom, left top, right top;
            }
            75% {
                background-position: left bottom, left top, right top, right bottom;
            }
            100% {
                background-position: left top, right top, right bottom, left bottom;
            }
        }
        
        .moving-dash-border {
            --border-width: 3px;
            --dash-length: 8px;
            --border-color: #1f708b;
            
            padding: 10px 20px;
            margin: 10px 0;
            text-align: center;
            position: relative;
            background: 
                linear-gradient(90deg, var(--border-color) 50%, transparent 50%) repeat-x top,
                linear-gradient(180deg, var(--border-color) 50%, transparent 50%) repeat-y right,
                linear-gradient(270deg, var(--border-color) 50%, transparent 50%) repeat-x bottom,
                linear-gradient(0deg, var(--border-color) 50%, transparent 50%) repeat-y left;
            background-size: 
                var(--dash-length) var(--border-width),
                var(--border-width) var(--dash-length),
                var(--dash-length) var(--border-width),
                var(--border-width) var(--dash-length);
            animation: border-dance 2s infinite linear;
        }
        </style>
        <div class="moving-dash-border">
            <b>Made with ❤️ by Con Bo Thui</b>
        </div>
    """,
        unsafe_allow_html=True,
    )


# --- RUN NAVIGATION ---
pg.run()
