import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO


# Nhập khoảng thời gian
st.title("Chia dữ liệu thành các khoảng thời gian và tải xuống CSV")
num_periods = st.number_input(
    "Số lượng khoảng thời gian muốn tách", min_value=1, step=1
)

periods = []
for i in range(num_periods):
    start_date = st.date_input(f"Ngày bắt đầu khoảng {i + 1}", datetime.today())
    end_date = st.date_input(
        f"Ngày kết thúc khoảng {i + 1}", datetime.today() + timedelta(days=1)
    )
    periods.append((start_date, end_date))
