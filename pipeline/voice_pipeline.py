from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
from database.database import get_all_students
import streamlit as st
import io
import librosa


@st.cache_resource
def voice_recognition_pipeline():
    recognizer = VoiceEncoder()
    return recognizer


def extract_voice_embeddings(audio_file):
    """Embed a SINGLE-speaker recording into one voice fingerprint (used at enrollment)."""
    try:
        recognizer = voice_recognition_pipeline()
        audio, _ = librosa.load(io.BytesIO(audio_file.read()), sr=16000)
        wav = preprocess_wav(audio, source_sr=16000)
        embedding = recognizer.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        st.error(f"Error processing audio file: {e}")
        return []


def voice_recognition(new_embedding, threshold=0.35, students=None):
    """Find the enrolled student whose stored voice fingerprint is closest to `new_embedding`.

    Returns (student_id, similarity). student_id is None if nothing clears the threshold.
    Pass `students` to avoid re-querying the DB on every call.
    """
    if students is None:
        students = get_all_students()

    best_match_student_id = None
    best_match_score = -1

    if not students:
        st.warning("No student data found. Please add students to the database.")
        return None, best_match_score

    # Track the closest match across ALL students (regardless of threshold)
    # so the caller can see how close we got even when nothing crosses the bar.
    closest_id = None
    closest_score = -1
    for student in students:
        embeddings = student.get("voice_embedding")
        if embeddings:
            stored_embedding = np.array(embeddings)
            similarity = np.dot(new_embedding, stored_embedding)
            if similarity > closest_score:
                closest_score = similarity
                closest_id = student.get("student_id")

    if closest_score >= threshold:
        return closest_id, closest_score
    return None, closest_score


def mark_voice_attendance(audio_file, students , threshold=0.35, top_db=30, min_seconds=1.0):
    """Roll-call attendance from ONE recording where students say "present" one at a time.

    Logic:
      1. Load the audio at 16 kHz.
      2. Split on the silent pauses  -> one chunk per student's utterance.
      3. Embed each chunk            -> a voice fingerprint.
      4. Match each fingerprint to the closest enrolled student (cosine similarity).
      5. Above threshold -> mark present (never counting a student twice).

    Returns a dict: {student_id: confidence_score}.
    """
    try:
        recognizer = voice_recognition_pipeline()
        audio, sr = librosa.load(io.BytesIO(audio_file.read()), sr=16000)
    except Exception as e:
        st.error(f"Error loading audio file: {e}")
        return {}

    if not students:
        students = get_all_students()
        st.warning("No student data found. Please add students to the database.")
        return {}

    present = {}                              # student_id -> best similarity score
    min_samples = int(min_seconds * 16000)    # ignore clips shorter than ~1s
    debug_lines = []

    # librosa.effects.split returns [start, end] sample ranges of the non-silent parts.
    # The pauses between students become the cut points -> one segment per utterance.
    intervals = librosa.effects.split(audio, top_db=top_db)
    debug_lines.append(f"librosa.effects.split found **{len(intervals)}** speech segment(s) at top_db={top_db}.")

    for start, end in intervals:
        segment = audio[start:end]
        duration = (end - start) / 16000
        if len(segment) < sr * 0.5:       # skip coughs / noise / half-words
            debug_lines.append(f"• {start/16000:.2f}s–{end/16000:.2f}s ({duration:.2f}s) — too short (<{min_seconds}s), skipped")
            continue

        wav = preprocess_wav(segment, source_sr=16000)
        embedding = recognizer.embed_utterance(wav)

        student_id, score = voice_recognition(embedding, threshold=threshold, students=students)
        verdict = "✅ matched" if student_id is not None else f"❌ below threshold ({threshold})"
        debug_lines.append(
            f"• {start/16000:.2f}s–{end/16000:.2f}s ({duration:.2f}s) — closest similarity = **{score:.3f}** → {verdict}"
        )
        if student_id is not None:
            # keep the highest-confidence match; never count the same student twice
            if student_id not in present or score > present[student_id]:
                present[student_id] = float(score)

    # Surface debug info so the user can SEE what scores were computed.
    with st.expander("🔍 Voice matching details", expanded=not present):
        for line in debug_lines:
            st.markdown(line)

    return present
