import streamlit as st
from database.database import get_all_students, create_student , get_student_subjects , get_student_attendance_logs , unenroll_student_from_subject
from src.ui.base_layout import style_dashboard_layout , style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_main
from PIL import Image
import numpy as np
from pipeline.face_pipeline import attendance_marking_pipeline, extract_face_embeddings , train_face_recognition_model , update_model
from pipeline.voice_pipeline import extract_voice_embeddings
from src.components.subject_card import subject_card
from src.components.enroll_in_subject import enroll_in_subject_dialog 
from src.components.auto_enroll_subject import auto_enroll_subject_id
from database.config import supabase
import time
def student_dashboard():
    st.title(f"""Welcome, {st.session_state.student_details['name']}!""")
    style_dashboard_layout()
    style_base_layout()
    c1 , c2 = st.columns(2 , vertical_alignment="center" , gap = "xxlarge")

    with c1:
        header_dashboard()
    with c2:
        if st.button("Logout" , type="secondary" , key = "logoutbutton" , shortcut="ctrl + backspace"):
            st.session_state.update({'logged_in': False, 'role': None, 'teacher': None})
            st.rerun()

    st.space(2)

    c1, c2 = st.columns(2 , vertical_alignment="center" , gap = "xxlarge")
    with c1:
        st.header("Your Enrolled Subjects")
    # Here you can add more details about the student's attendance, such as a table of past attendance records, etc.
    with c2:
        if st.button("Enroll in a new subject" , type="primary" , key = "enrollbutton"):
            enroll_in_subject_dialog()

    st.spinner("Loading your subjects and attendance records...")
    # You would replace the following with actual data retrieval and display logic
    subjects = get_student_subjects(st.session_state.student_details["student_id"])
    logs = get_student_attendance_logs(st.session_state.student_details["student_id"])

    stats = {}
    for log in logs:
        subject_id = log["subject_id"]
        if subject_id not in stats:
            stats[subject_id] = {"present": 0, "total": 0, "subject_info": log.get("subjects", {})}
        if log["is_present"]:
            stats[subject_id]["present"] += 1
        stats[subject_id]["total"] += 1

    def unenroll_button():
        if st.button("Unenroll" , type="tertiary" , key = f"unenroll_{subject['subject_id']}" , icon = ":material/remove:"):
            res = unenroll_student_from_subject(subject["subject_id"] , st.session_state.student_details["student_id"])
            if res:
                st.success(f"Successfully unenrolled from {subject['subjects']['name']}!")
                time.sleep(2)  # Pause briefly to show the success message before rerunning
                st.rerun()  # Refresh the page to show the updated list of enrolled subjects
            else:
                st.error("An error occurred while unenrolling. Please try again later.")
    col = st.columns(2, gap="large")
    for i , subject in enumerate(subjects):
        subject_id = subject["subject_id"]
        stats_subject = stats.get(subject_id, {"present": 0, "total": 0})
        with col[i%2]:
            subject_card(
                name=subject["subjects"]["name"],
                code=subject["subjects"]["subject_code"],
                section=subject["subjects"]["section"],
                stats = [
                    ["✅" , "Present" , stats_subject["present"]],
                    ["📅" , "Total" , stats_subject["total"]]
                ],
                footer_callback = unenroll_button
            )
        

def student_register():
    c1 , c2 = st.columns(2 , vertical_alignment="center" , gap = "xxlarge")
    with c1:
        header_dashboard()
    with c2:
        st.button("Back to Login" , type="secondary" , on_click=lambda : st.session_state.update({'register_new_student': False}) , key = "registerbackbutton")

    st.header("Register as a New Student")
    st.space(2)

    name = st.text_input("Full Name" , placeholder="Enter your full name" , key="register_student_name")
    picture = st.camera_input("Capture your face" , key="register_face_input")
    voice_audio = st.audio_input("Optional: say \"present\" to enable voice attendance" , key="register_voice_input")

    if st.button("Create Profile" , type="primary" , key="submit_registration"):
        if not name:
            st.error("Please enter your name.")
        elif picture is None:
            st.error("A face photo is required to register.")
        else:
            with st.spinner("Creating a new student profile..."):
                arr = np.array(Image.open(picture))
                face_embeddings = extract_face_embeddings(arr)
                if len(face_embeddings) != 1:
                    st.error("Couldn't detect a single clear face. Please retake the photo.")
                else:
                    face_embedding = face_embeddings[0].tolist()

                    voice_embedding = None
                    if voice_audio is not None:
                        extracted = extract_voice_embeddings(voice_audio)
                        if extracted:
                            voice_embedding = extracted

                    response_data = create_student(name, face_embedding, voice_embedding)
                    if response_data:
                        update_model()  # Clear the cache and retrain so the newly-registered student is matchable
                        st.session_state["register_new_student"] = False
                        st.session_state.role = "student"
                        st.session_state.logged_in = True
                        st.session_state.student_details = response_data[0]
                        st.success(f"welcome back {response_data[0]['name']}!")
                    else:
                        st.error("An error occurred while creating your profile. Please try again.")
                    st.success(f"Profile created for {name}! Go back and log in with your face.")
                    st.rerun()

def student_screen():
    style_dashboard_layout()
    style_base_layout()
    if st.session_state.get("logged_in") and st.session_state.get("role") == "student":
        student_dashboard()
        return

    if st.session_state.get("register_new_student"):
        student_register()
        footer_main()
        return

    c1 , c2 = st.columns(2 , vertical_alignment="center" , gap = "xxlarge")

    with c1:
        header_dashboard()
    with c2:
        st.button("Go back to Home" , type="secondary" , on_click=lambda : st.session_state.update({'login_type':None}) , key = "loginbackbutton" , shortcut="ctrl + backspace")

    st.header("Login using Face ID")
    st.space(2)


    img = st.camera_input("Capture your image for attendance marking" , key = "student_camera_input")
    register_now = False
    if img:
        arr = np.array(Image.open(img)) # Here you can add your logic to process the captured image and mark attendance
        with st.spinner("Processing your image..."):
            student , n , number_of_faces = attendance_marking_pipeline(arr)
            if number_of_faces == 0:
                st.warning("No recognizable face detected. Please try again.")
            elif number_of_faces > 1:
                st.warning("number of faces detcted are greater than 1. Please try again with only one face in the frame.")
            else:
                if student :
                    student_id = list(student.keys())[0]
                    all_students = get_all_students()
                    stud = next((s for s in all_students if s['student_id'] == student_id), None)
                    if stud:
                        st.session_state.role = "student"
                        st.session_state.logged_in = True
                        st.session_state.student_details = stud
                        st.success(f"welcome back {stud['name']}!")
                        time.sleep(1)   # brief pause so the welcome message is visible
                        st.rerun()       # switch to the dashboard via the top guard
                    else:
                        st.error("Student record not found. Please contact administration.")
                else:
                    st.error("Face not recognized. Redirecting you to registration...")
                    register_now = True
    if register_now:
        st.session_state["register_new_student"] = True
        st.rerun()

    footer_main()
