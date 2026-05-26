import streamlit as st

def footer_main():

    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; gap: 10px; margin-top: 30px;">
        <p style="text-align: center; color: white;">© 2024 SnapClass. All rights
        reserved.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )   