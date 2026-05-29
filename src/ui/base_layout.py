import streamlit as st

def style_main_layout():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #5865F2 !important;
        }
        .stApp div[data-testid="stColumn"] {
            background-color: #E0E3FF !important;
            padding:2.5rem !important;
            border-radius: 5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def style_dashboard_layout():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #E0E3FF !important;
        }
        h2 {
            color: #5865F2 !important;  
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_base_layout():
    st.markdown(
        """        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

                
         /* Hide Top Bar of streamlit */
                
            #MainMenu, footer, header {
                visibility: hidden;
            }
                
            .block-container {
                padding-top:1.5rem !important;    
            }

            h1 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height:0.9 !important;
                margin-bottom:0rem !important;
            }
                

            h2 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height:0.9 !important;
                margin-bottom:0rem !important;
            }
                
            h3, h4, p {
                font-family: 'Outfit', sans-serif;    
            }
                

            button{
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            /* Keep every button's label on a single line — the button widens to fit. */
            button p {
                white-space: nowrap !important;
            }

            button[kind="secondary"]{
                border-radius: 1.5rem !important;
                background-color: #EB459E !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="tertiary"]{
                border-radius: 1.5rem !important;
                background-color: black !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button:hover{
                transform :scale(1.05)}

            /* Multiselect — white input area, readable on the colored background */
            .stMultiSelect div[data-baseweb="select"] > div {
                background-color: #ffffff !important;
                border-radius: 0.75rem !important;
            }
            .stMultiSelect div[data-baseweb="select"] * {
                color: #1e1e1e !important;
            }
            /* The selected "chips" inside the multiselect */
            .stMultiSelect span[data-baseweb="tag"] {
                background-color: #5865F2 !important;
            }
            .stMultiSelect span[data-baseweb="tag"] * {
                color: #ffffff !important;
            }

        </style>
        """ ,
        unsafe_allow_html=True,
    )