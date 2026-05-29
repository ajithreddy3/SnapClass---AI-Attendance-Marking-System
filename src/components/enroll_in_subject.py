import streamlit as st
from database.config import supabase
from database.database import student_enroll_subject
import time 
@st.dialog("Enroll in Subject")
def enroll_in_subject_dialog():
    st.write("To enroll in a new subject, please enter the subject code provided by your teacher.")
    subject_code = st.text_input("Subject Code", placeholder="Enter the subject code here", key="enroll_subject_code")

    if st.button("Enroll", type="primary", key="enroll_submit_button"):
        if not subject_code:
            st.error("Please enter a subject code to enroll.")
        else:
            # Here you would typically call a function to handle the enrollment logic,
            # such as verifying the subject code and adding the student to the class.
            # For this example, we'll just show a success message.
            res = supabase.from_("subjects").select("subject_id , name , subject_code").eq("subject_code", subject_code).execute()
            if res.data:
                subject_id = res.data[0]["subject_id"]
                subject_name = res.data[0]["name"]
                # You would also want to add the student to the subject's roster in the database here.
                is_enrolled = supabase.from_("subject_student").select("*").eq("subject_id", subject_id).eq("student_id", st.session_state.student_details["student_id"]).execute()
                if is_enrolled.data:
                    st.warning(f"You are already enrolled in {subject_name} (Code: {subject_code}).")
                else:
                    data = student_enroll_subject(subject_id , st.session_state.student_details["student_id"])
                    if data:
                        st.success(f"Successfully enrolled in {subject_name} (Code: {subject_code})!")
                        time.sleep(2)  # Pause briefly to show the success message before rerunning
                        st.rerun()  # Refresh the page to show the updated list of enrolled subjects
                    else:
                        st.error("An error occurred while enrolling. Please try again later.")
            else:   
                st.error("Invalid subject code. Please check with your teacher and try again.")
            st.success(f"Successfully enrolled in subject with code: {subject_code}")
