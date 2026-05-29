import streamlit as st
from database.database import check_teacher_exists , create_teacher , teacher_login , get_teacher_subjects , mark_attendance , get_teacher_attendance
from src.ui.base_layout import style_dashboard_layout , style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_main
from src.components.subject_card import subject_card
from src.components.share_subject import share_subject_dialog
from src.components.create_new_subject import create_new_subject_dialog
from database.database import create_teacher , check_teacher_exists , teacher_login
from src.components.add_photo import add_photo_dialog
from pipeline.face_pipeline import attendance_marking_pipeline
import numpy as np
from datetime import datetime
from database.config import supabase
from src.components.show_attendance_results import show_attendance_results_dialog
import pandas as pd
from src.components.voice_attendance import voice_attendance_dialog
def teacher_dashboard():
    st.title(f"""Welcome, {st.session_state.teacher['name']}!""")
    style_dashboard_layout()
    style_base_layout()
    c1 , c2 = st.columns(2 , vertical_alignment="bottom" , gap = "xxlarge" )

    with c1:
        header_dashboard()
    with c2:
        if st.button("Logout" , type="secondary" , key = "logoutbutton" , shortcut="ctrl + backspace"):
            st.session_state.update({'logged_in': False, 'role': None, 'teacher': None})
            st.rerun()

    st.space(2)
    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"
    tab1 , tab2 , tab3 = st.columns(3 , gap="large" , vertical_alignment= "bottom")
    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == "take_attendance" else "tertiary"
        if st.button("Attendance Marking" , type=type1 , key = "attendancemarkingtabbutton" , icon = ":material/ar_on_you:" , width= "stretch" , use_container_width=True):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == "manage_subjects" else "tertiary"
        if st.button("Manage Subjects" , type=type2 , key = "subjectstabbutton" , icon = ":material/people:" , width = "stretch"):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()
    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == "attendance_records" else "tertiary"
        if st.button("Attendance Records" , type=type3 , key = "attendancerecordstabbutton" , icon = ":material/cards_stack:" , width = "stretch" , use_container_width = True):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()

    if st.session_state.current_teacher_tab == "take_attendance":
        take_attendance_screen()
    elif st.session_state.current_teacher_tab == "manage_subjects":
        manage_subjects_screen()
    elif st.session_state.current_teacher_tab == "attendance_records":
        attendance_records_screen()
    
    footer_main()

def take_attendance_screen():
    teacher_id = st.session_state.teacher['teacher_id']
    subjects = get_teacher_subjects(teacher_id)
    st.header("Take AI Attendance")
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
    if not subjects:
        st.info("You haven't created any subjects yet. Click on the 'Manage Subjects' tab to add a subject before taking attendance.")
        return
    else:
        subject_options = {f"{sub['name']} - {sub['section']}": sub['subject_id'] for sub in subjects}
        c1, c2 = st.columns(2 , vertical_alignment="bottom" , gap = "xxlarge" )
        with c1:
            st.write("Select Subject and Take Attendance")
            selected_subject_name = st.selectbox("Select Subject", options=list(subject_options.keys()))
        with c2:
            if st.button("Take Attendance" , type="primary" , key = "takeattendancebutton" , icon = ":material/ar_on_you:" , width="stretch"):
                add_photo_dialog()
            
        selected_subject_id = subject_options[selected_subject_name]
        attendance_cols = st.columns(4)

        for idx, col in enumerate(st.session_state.get('attendance_images', [])):
            with attendance_cols[idx % 4]:
                st.image(col, caption=f"Attendance Photo {idx + 1}", width = "stretch")
            
        col1 , col2 , col3 = st.columns(3 , gap="large")
        with col1:
            if st.button("clear photos" , type="secondary" , key = "clearphotosbutton" , icon = ":material/delete:" , width="stretch") :
                st.session_state['attendance_images'] = []
                st.rerun()
            
        with col2:
            if st.button("Mark Attendance" , type="secondary" , key = "markattendancebutton" , icon = ":material/analytics:" , width="stretch") :
                if not st.session_state.get('attendance_images'):
                    st.warning("Please add at least one photo before marking attendance.")
                else:
                    # Aggregate detections across ALL photos into one dict BEFORE doing anything else.
                    all_detected_ids = {}
                    with st.spinner("Recognising students across all photos..."):
                        for idx , img in enumerate(st.session_state['attendance_images']):
                            np_img = np.array(img.convert('RGB'))
                            detected_students , unrecognized_count , total_faces = attendance_marking_pipeline(np_img)
                            if detected_students:
                                for student_id in detected_students.keys():
                                    sid = int(student_id)
                                    all_detected_ids.setdefault(sid, []).append(f"Photo {idx + 1}")

                    # Fetch the roster ONCE, build the results table ONCE, open the dialog ONCE.
                    enrolled_students = supabase.table("subject_student").select("* , students(*)").eq("subject_id", selected_subject_id).execute()
                    enrolled_students_data = enrolled_students.data
                    if not enrolled_students_data:
                        st.warning(f"No students are enrolled in {selected_subject_name}. Please enroll students before marking")
                    else:
                        results , attendance_logs = [] , []
                        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for node in enrolled_students_data:
                            student = node.get("students", {})
                            student_id = node.get("student_id")
                            source = all_detected_ids.get(student_id, [])
                            is_present = len(source) > 0
                            results.append({
                                "student_id": student_id,
                                "name": student.get("name", "N/A"),
                                "status": "Present" if is_present else "Absent",
                                "source": ", ".join(source) if source else "Not Detected",
                            })
                            attendance_logs.append({
                                "student_id": student_id,
                                "subject_id": selected_subject_id,
                                "is_present": is_present,
                                "timestamp": current_timestamp,
                            })
                        show_attendance_results_dialog(pd.DataFrame(results) , attendance_logs)
        with col3:
            if st.button("voice Attendance" , width = "stretch" , icon = ":material/mic:"):
                voice_attendance_dialog(selected_subject_id)      

def manage_subjects_screen():
    teacher_id = st.session_state.teacher['teacher_id']
    col1 , col2 = st.columns(2)
    with col1:
        st.header("Manage Your Subjects and Classes")
    with col2:
        if st.button("Add New Subject" , type="primary" , key = "addsubjectbutton" , icon = ":material/add:" , width="stretch"):
            create_new_subject_dialog(teacher_id)
    
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for subject in subjects:
            stats = [
                ("👥", "Students", subject.get("total_students", 0)),
                ("📅", "Classes", subject.get("num_of_classes", 0)),
            ]

            st.space(2)

            def share_class(subject=subject):
                if st.button("Share Class" , type="secondary" , key = f"share_{subject['subject_id']}" , icon = ":material/share:" , width="stretch"):
                    share_subject_dialog(subject["name"] , subject["subject_id"])

            subject_card(
                name = subject.get("name", "N/A"),
                code = subject.get("subject_code", "N/A"),
                section = subject.get("section", "N/A"),
                stats = stats,
                footer_callback = share_class,
            )
    else:
        st.info("You haven't created any subjects yet. Click the 'Add New Subject' button")
                    
            # Here you can add more details about the subject, such as a list of students, attendance records, etc.

def attendance_records_screen():
    st.header("View and Export Attendance Records")
    teacher_id = st.session_state.teacher['teacher_id']

    response = get_teacher_attendance(teacher_id)
    if not response:
        st.info("No attendance records yet. Take attendance in any subject to start building records here.")
        return

    # Total enrolled per subject — gives us the denominator for "X / Y".
    total_students_by_subject = {
        s["subject_id"]: s.get("total_students", 0)
        for s in get_teacher_subjects(teacher_id)
    }

    # Group the flat attendance rows into one row per (subject, session timestamp).
    sessions = {}
    for r in response:
        key = (r.get("subject_id"), r.get("timestamp"))
        if key not in sessions:
            subj = r.get("subjects") or {}
            sessions[key] = {
                "subject_id": r.get("subject_id"),
                "subject_name": subj.get("name", "Unknown"),
                "subject_section": subj.get("section", ""),
                "subject_code": subj.get("subject_code", ""),
                "timestamp": r.get("timestamp"),
                "present_count": 0,
            }
        if r.get("is_present"):
            sessions[key]["present_count"] += 1

    df = pd.DataFrame([
        {
            "Date": (s["timestamp"] or "")[:10],
            "Time": (s["timestamp"] or "")[11:19],
            "Subject": f"{s['subject_name']} - {s['subject_section']}",
            "Subject Code": s["subject_code"],
            "Attendance": f"{s['present_count']} / {total_students_by_subject.get(s['subject_id'], '?')}",
        }
        for s in sessions.values()
    ]).sort_values(["Date", "Time"], ascending=[False, False]).reset_index(drop=True)

    # Optional filter by subject so the teacher can focus on one class.
    available_subjects = sorted(df["Subject"].unique())
    selected_subjects = st.multiselect("Filter by subject", available_subjects, default=available_subjects)
    df_filtered = df[df["Subject"].isin(selected_subjects)]

    st.caption(
        f"Showing **{len(df_filtered)}** session(s) across **{df_filtered['Date'].nunique()}** date(s)."
    )
    st.dataframe(df_filtered, hide_index=True, width="stretch")

    # CSV export of whatever the teacher has filtered to.
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download as CSV",
        data=csv_bytes,
        file_name="attendance_records.csv",
        mime="text/csv",
        icon=":material/download:",
    )



def tlogin(username, password):
    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.teacher = teacher
        st.session_state.role = 'teacher'
        st.session_state.logged_in = True
        return True
    return False
def teacher_screen():
    if st.session_state.get('logged_in') and st.session_state.get('role') == 'teacher':
        teacher_dashboard()       # already renders footer_main() internally
        return
    if 'teacher_screen_state' not in st.session_state or st.session_state['teacher_screen_state'] is None:
        st.session_state['teacher_screen_state'] = 'login'
    if st.session_state['teacher_screen_state'] == 'login':
        teacher_screen_login()
    elif st.session_state['teacher_screen_state'] == 'register':
        teacher_screen_register()

    footer_main()

def Register_teacher(username , name , password , confirm_password):
    if not username or not name or not password or not confirm_password:
        return False , "All fields are required."
    if check_teacher_exists(username):
        return False , "Username already exists. Please choose a different username."
    if password != confirm_password:
        return False , "Passwords do not match."
    
    try :
        teacher_data = create_teacher(username , name , password)
        if teacher_data:
            return True , "Registration successful. You can now log in with your credentials."
        else:
            return False , "An error occurred during registration. Please try again."
    except Exception as e:
        return False , "Unexpected Error"
    # Here you can add your logic to save the teacher's information to the database
    # For example, you can use Supabase or any other database service to store the teacher's data

    return True , "Registration successful. You can now log in with your credentials."
def teacher_screen_login():
    style_dashboard_layout()
    style_base_layout()
    c1 , c2 = st.columns(2 , vertical_alignment="center" , gap = "xxlarge")

    with c1:
        header_dashboard()
    with c2:
        st.button("Go back to Home" , type="secondary" , on_click=lambda : st.session_state.update({'login_type':None}) , key = "loginbackbutton" , shortcut="ctrl + backspace")

    st.header("Login With Your Teacher Profile")

    st.space(2)
    teacher_username = st.text_input("Username" , placeholder="Enter your username" , key="login_username")
    teacher_password = st.text_input("Password" , placeholder="Enter your password" , type="password" , key="login_password")

    st.divider()
    btn_col1 , btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Login" , type="primary" , shortcut="control + enter" , icon = ":material/passkey:" , width= "stretch"):
            if tlogin(teacher_username, teacher_password):
                st.toast("Login successful!" , icon="✅")
                st.rerun()
                # Here you can add your logic to set the teacher's session or authentication state
                # For example, you can set a session variable to indicate that the teacher is logged in
                # st.session_state['teacher_logged_in'] = True
            else:
                st.error("Invalid username or password. Please try again.")
            # Here you can add your authentication logic
    with btn_col2:
        if st.button("Register Instead" , type="secondary" , icon = ":material/passkey:" , key = "teacherregisterbutton" , width="stretch"):
            st.session_state['teacher_screen_state'] = 'register'
            st.rerun()

def teacher_screen_register():
    style_dashboard_layout()
    style_base_layout()
    c1 , c2 = st.columns(2 , vertical_alignment="center" , gap = "xxlarge")

    with c1:
        header_dashboard()
    with c2:
        st.button("Go back to Home" , type="secondary" , icon = ":material/passkey:" , on_click=lambda : st.session_state.update({'login_type':None}) , key = "registerbackbutton" , shortcut="ctrl + backspace")

    st.header("Register With Your Teacher Profile")
    st.space(2)
    teacher_username = st.text_input("Username" , placeholder="Enter your username" , key="register_username")
    teacher_name = st.text_input("Full Name" , placeholder="Enter your full name" , key="register_name")
    teacher_password = st.text_input("Password" , placeholder="Enter your password" , type="password" , key="register_password")
    teacher_confirm_password = st.text_input("Confirm Password" , placeholder="Re-enter your password" , type="password" , key="register_confirm_password")

    st.divider()
    btn_col1 , btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Register" , type="primary" , shortcut="control + enter" , icon = ":material/passkey:" , width= "stretch"):
            success , message = Register_teacher(teacher_username , teacher_name , teacher_password , teacher_confirm_password)
            if success:
                st.success(message)
                import time
                time.sleep(2)
                st.session_state['teacher_screen_state'] = 'login'
                st.rerun()
            else:
                st.error(message)
                import time
                time.sleep(2)                
                st.session_state['teacher_screen_state'] = 'register'
                st.rerun()
            # Here you can add your authentication logic
    with btn_col2:
        if st.button("Login Instead" , type="secondary" , icon = ":material/passkey:" , key = "teacherloginbutton" , width="stretch"):
            st.session_state['teacher_screen_state'] = 'login'
            st.rerun()