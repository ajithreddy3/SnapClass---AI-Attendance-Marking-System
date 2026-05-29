import streamlit as st
import time
import numpy as np
from PIL import Image
from pipeline.face_pipeline import attendance_marking_pipeline
from database.database import mark_attendance, get_all_students


@st.dialog("Mark Attendance")
def add_photo_dialog():
    
    """Take or upload a class photo, recognise faces, and mark attendance for `subject_id`."""
    if 'photo_source' not in st.session_state:
        st.session_state['photo_source'] = 'camera'
    tab1, tab2 = st.columns(2)
    with tab1:
        camera_type = 'primary' if st.session_state['photo_source'] == 'camera' else 'tertiary'
        if st.button("Take a photo", type=camera_type):
            st.session_state['photo_source'] = 'camera'
    with tab2:
        upload_type = 'primary' if st.session_state['photo_source'] == 'upload' else 'tertiary'
        if st.button("Upload a photo", type=upload_type):
            st.session_state['photo_source'] = 'upload'

    if st.session_state['photo_source'] == 'camera':
        photo = st.camera_input("Take a photo of the class")
        if photo:
            st.session_state.attendance_images.append(Image.open(photo))
            st.toast("Photo added successfully!", icon="✅")
            st.rerun()

    elif st.session_state['photo_source'] == 'upload':
        photo = st.file_uploader("Upload a photo of the class", type=["jpg", "jpeg", "png"] , accept_multiple_files=True , key="file_uploader")
        if photo:
            for img in photo:
                st.session_state.attendance_images.append(Image.open(img))
            st.toast("Photos added successfully!", icon="✅")

    st.divider()

    if st.button("Mark Attendance", type="primary"):
        st.rerun()
        