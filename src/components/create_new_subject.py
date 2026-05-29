import streamlit as st
from database.database import create_new_subject
@st.dialog("create_new_subject_dialog")
def create_new_subject_dialog(teacher_id):
    st.write("Enter the details for the new subject:")
    subject_name = st.text_input("Subject Name" , placeholder="Enter the name of the subject")
    subject_code = st.text_input("Subject Code" , placeholder="Enter the code for the subject")
    section = st.text_input("Section" , placeholder="Enter the section for the subject")
    if st.button("Create Subject" , type="primary" , shortcut="control + enter" , icon = ":material/add:" , width= "stretch"):
        if subject_name and subject_code and section:
            try:
                response = create_new_subject(subject_name, subject_code, section , teacher_id=teacher_id)
                if response:
                    st.toast("Subject created successfully!" , icon="✅")
                    st.rerun()
                else:
                    st.error("Failed to create subject. Please try again.")
            except Exception as e:
                st.error(f"An error occurred while creating the subject: {e}")
        else:
            st.warning("Please fill in all the details to create a new subject.")