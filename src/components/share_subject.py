import streamlit as st
import segno
import io


@st.dialog("Share Class")
def share_subject_dialog(subject_name, subject_id):
    app_domain = "snapclass-main.streamlit.app"  # Change this to your Streamlit app's domain if different
    join_url = f"{app_domain}/?join_subject={subject_id}"

    st.write(f"Share **{subject_name}** with your students using the QR code or the link below.")

    # Generate the QR code as a PNG into an in-memory buffer (no temp file needed).
    # error='h' = high error correction (more robust if the QR gets partly hidden).
    qr = segno.make(join_url, error='h')
    buffer = io.BytesIO()
    qr.save(buffer, kind='png', scale=8, border=2)
    buffer.getvalue()

    col1, col2 = st.columns([1, 1.2], vertical_alignment="center")
    with col1:
        st.image(buffer, caption="Scan to join")
    with col2:
        st.write("**Join link**")
        st.code(join_url, language="English")
        st.caption("Students can scan the QR or open this link to join the class.")
