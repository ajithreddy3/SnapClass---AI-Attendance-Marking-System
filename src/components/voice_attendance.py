import streamlit as st
from datetime import datetime
from pipeline.voice_pipeline import mark_voice_attendance
from database.database import mark_attendance, get_all_students
from database.config import supabase
import pandas as pd 


@st.dialog("Voice Attendance")
def voice_attendance_dialog(subject_id):
    """Record or upload audio of students saying 'present' one by one, then mark attendance."""
    st.write(
        "Record or upload an audio clip in which students say "
        "**\"present\"** one at a time, with a brief pause between each."
    )
    if 'voice_attendance_results' not in st.session_state:
        st.session_state.voice_attendance_results = None
    enrolled_students = supabase.table("subject_student").select("* , students(*)").eq("subject_id", subject_id).execute()
    if not enrolled_students.data:
        st.error("No students enrolled in the subject")
        return
    students = [
        row["students"]
        for row in enrolled_students.data
        if row["students"].get("voice_embedding")   # keep only students who have a voice embedding
    ]
    # Two ways to provide the audio.
    if not students :
        st.error("No Students enrolled in the class has thier voice registered")
        return
    tab1, tab2 = st.tabs(["Record", "Upload"])
    audio = None
    with tab1:
        recorded = st.audio_input("Record the roll-call audio", key="voice_record_input")
        if recorded is not None:
            audio = recorded
    with tab2:
        uploaded = st.file_uploader(
            "Upload an audio file",
            type=["wav", "mp3", "ogg", "m4a"],
            key="voice_upload_input",
        )
        if uploaded is not None:
            audio = uploaded

    if audio is None:
        st.info("Record or upload audio, then click Mark Attendance.")
        return

    st.audio(audio)

    if st.button("Mark Attendance", type="primary", icon=":material/check:", width="stretch"):
        with st.spinner("Recognising voices..."):
            present = mark_voice_attendance(audio , students)   # {student_id: confidence}

        if not present:
            st.warning("No enrolled students' voices were recognised in the audio.")
        else:
            # One row per present student, all sharing the same timestamp = one session.
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records = [
                {
                    "subject_id": subject_id,
                    "student_id": sid,
                    "is_present": True,
                    "timestamp": timestamp,
                }
                for sid in present.keys()
            ]
            logs = [{
                "Name": next((s["name"] for s in students if s["student_id"] == sid), "Unknown"),
                "student_id": sid,
                "is_present": "✅ Present",
                "source" : present[sid],

            } for sid in present.keys()]
            # Stash for the results panel below — survives reruns so Confirm/Discard keep working.
            # NOTE: no st.rerun() here — that would close the dialog. The function naturally
            # falls through to the results panel a few lines below, which renders in this same run.
            st.session_state['voice_attendance_results'] = (records, logs)

    # ----- Results panel -----
    # Rendered on every run (not inside the Mark Attendance click block) so the
    # Confirm/Discard buttons actually exist on the run their clicks fire on.
    if st.session_state.get('voice_attendance_results'):
        records, logs = st.session_state['voice_attendance_results']
        st.divider()
        st.subheader("Attendance Results")
        st.dataframe(pd.DataFrame(logs), hide_index=True, width="stretch")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Discard", type="tertiary", key="voice_discard"):
                st.session_state['voice_attendance_results'] = None
                st.toast("Attendance discarded.", icon="❌")
                st.rerun()
        with d2:
            if st.button("Confirm", type="primary", key="voice_confirm"):
                if mark_attendance(records):
                    st.session_state['voice_attendance_results'] = None
                    st.toast("Attendance marked successfully!", icon="✅")
                    st.rerun()
                else:
                    st.error("Some error occurred while marking attendance.")