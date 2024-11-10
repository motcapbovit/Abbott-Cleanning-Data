import streamlit as st


if "df" not in st.session_state or st.session_state.df is None:
    st.write("Chua co data cua df")
else:
    st.write("Da co data roi nhe")
    df = st.session_state.df
    st.dataframe(df)
