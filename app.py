import streamlit as st
from src.screen.home_screen import home_screen
from src.screen.teacher_screen import teacher_screen
from src.screen.student_screen import student_screen
def main():

    st.set_page_config(
        page_title= "SnapClass - AI Attendance Marking System" ,
        page_icon= "https://i.ibb.co/YTYGn5qV/logo.png"
    )

    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None
    
    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()
        case 'student':
            student_screen()
        case None:
            home_screen()


join_subject = st.query_params.get('join-subject')
if join_subject:
    if st.session_state.login_type != 'student':
        st.session_state.login_type = 'student'
        st.rerun()
    if st.session_state.get('logged_in') and st.session_state.get('role') == 'student':
            auto_enroll_dialog(join_subject)

if __name__ == "__main__":
    main()