import streamlit as st

from supabase import create_client, Client


supabase: Client = create_client(st.secrets["SUPA_BASE_URL"], st.secrets["SUPABASE_KEY"])