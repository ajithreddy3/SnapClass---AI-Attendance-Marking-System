import streamlit as st

from database.database import mark_attendance

@st.dialog("Attendance Results")
def attendance_dialog(df , attendance_logs) :
    st.header(f"Attendance Results")
    st.dataframe(df , hide_index=True , width = "stretch")
    c1 , c2 = st.columns(2)
    with c1:
        if st.button("Discard", type="tertiary") :
            st.toast("Attendance discarded.", icon="❌")
            st.session_state.attendance_images = []
            st.session_state.voice_attendance_results = []
            st.rerun()
    with c2:
        if st.button("Confirm", type="primary"):
            response = mark_attendance(attendance_logs)   # pass the WHOLE list once
            if response:                                   # mark_attendance returns the inserted rows (or [])
                st.session_state.attendance_images = []
                st.session_state.voice_attendance_results = []
                st.session_state.voice_attendance
                st.toast("Attendance marked successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Some Error Occurred While Marking Attendance")


def show_attendance_results_dialog(df , attendance_logs):
    attendance_dialog(df , attendance_logs)