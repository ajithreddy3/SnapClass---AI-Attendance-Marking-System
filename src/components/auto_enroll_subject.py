import time

import streamlit as st
import supabase
from database.config import supabase
from database.database import student_enroll_subject
"""This component handles the auto-enrollment of students into subjects when they click on a join link or scan a QR code that contains the subject code. It defines a dialog that is triggered when a student tries to join a subject using the provided code. The dialog will attempt to enroll the student in the subject and provide feedback on whether the enrollment was successful or if there were any issues (e.g., invalid code, already enrolled, etc.)."""
@st.dialog("Auto Enroll in Subject")
def auto_enroll_subject_id(join_subject):
    student_id = st.session_state.student_details["student_id"]
    subject_id = join_subject # Assuming the subject ID is passed as a query parameter

    res = supabase.from_("subjects").select("name , subject_code").eq("subject_id", join_subject).execute()
    if res.data:
        is_enrolled = supabase.from_("subject_student").select("*").eq("subject_id", join_subject).eq("student_id", st.session_state.student_details["student_id"]).execute()
        if is_enrolled.data:
            st.warning(f"You are already enrolled in {res.data[0]['name']} (Code: {res.data[0]['subject_code']}).")
            st.button("Close" , type = "primary")
            st.query_params.clear()  # Clear query params to prevent re-triggering
        else:
            st.markdown(f"""Would you like to enroll in **{res.data[0]['name']}** using the code **{join_subject}**?""")
            if st.button("Enroll", type="primary"):
                data = student_enroll_subject(subject_id , student_id)
                if data:
                    st.success(f"Successfully enrolled in {res.data[0]['name']} (Code: {join_subject})!")
                    time.sleep(2)  # Pause briefly to show the success message before rerunning
                    st.query_params.clear()  # remove join_subject from URL so the dialog doesn't re-trigger
                    st.rerun()  # Refresh the page to show the updated list of enrolled subjects
                else:
                    st.error("An error occurred while enrolling. Please try again later.")
    else:
        st.error("Invalid subject code. Please check with your teacher and try again.")
        st.button("Close" , type = "primary")
        st.query_params.clear()  # Clear query params to prevent re-triggering

