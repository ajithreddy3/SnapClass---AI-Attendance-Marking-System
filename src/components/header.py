import streamlit as st

def header_main():

    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; gap: 10px; margin-top: 30px;">
        <img src="{logo_url}" alt="Logo" style="width: 100px; height: 100px;">
        <h1 style="text-align: center; color: white; ">Snap <br>Class</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
