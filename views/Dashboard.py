import streamlit as st


if st.session_state.df is None or "df" not in st.session_state:
    st.write("Chua co data cua df")
else:
    st.write("Da co data roi nhe")
    df = st.session_state.df
    st.dataframe(df)
