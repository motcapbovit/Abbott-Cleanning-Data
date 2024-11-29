import streamlit as st
import pandas as pd

upload_file = st.file_uploader("Choose your data file (CSV format)", type="xlsx")

if upload_file:
    df = pd.read_excel(upload_file)
    df["start_date"] = pd.to_datetime(df["start_date"], format="%d/%m/%Y %H:%M:%S")
    df["end_date"] = pd.to_datetime(df["end_date"], format="%d/%m/%Y %H:%M:%S")

    for i in len(df):
        if df["start_date"].iloc[i] < min_date:
            less_than_min_date.append(df["start_date"].iloc[i])
        if df["end_date"].iloc[i] > max_date:
            more_than_max_date.append(df["end_date"].iloc[i])
    
    print("Danh sasch cac ngay khong hop le:")
    print(less_than_min_date)
    print(more_than_max_date)


    st.write(df)
