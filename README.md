# SnapClass — AI Attendance Marking System

SnapClass is an AI-powered attendance system built with [Streamlit](https://streamlit.io/). Teachers create subjects and mark attendance for an entire class in seconds — either by snapping a **photo of the room** (face recognition) or by recording a short **roll-call audio clip** (voice recognition). Students register their face (and optionally their voice) once, then log in with Face ID and join classes by scanning a QR code or opening a share link.

No manual roll calls. No spreadsheets. Just a photo or a recording.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
  - [Face Recognition Pipeline](#face-recognition-pipeline)
  - [Voice Recognition Pipeline](#voice-recognition-pipeline)
- [Tech Stack](#tech-stack)
- [Architecture & Project Structure](#architecture--project-structure)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Supabase Setup](#supabase-setup)
  - [Configuring Secrets](#configuring-secrets)
  - [Running the App](#running-the-app)
- [User Guide](#user-guide)
  - [For Teachers](#for-teachers)
  - [For Students](#for-students)
- [Deployment](#deployment)
- [Notes & Limitations](#notes--limitations)
- [License](#license)

---

## Features

### 👩‍🏫 Teacher
- **Register & log in** with a username/password (passwords are hashed with `bcrypt`).
- **Create subjects** with a name, subject code, and section.
- **Share a class** via an auto-generated **QR code** and join link — students join in one tap.
- **Mark attendance by photo** — take or upload one or more class photos; the system detects every face, matches each against enrolled students, and produces a Present/Absent table before you confirm.
- **Mark attendance by voice** — record/upload a roll-call clip where students say *"present"* one at a time; the system splits the audio per speaker and identifies each voice.
- **Review attendance records** grouped per session, filter by subject, and **export to CSV**.

### 🎓 Student
- **Register once** with a webcam face capture and an optional voice sample.
- **Log in with Face ID** — no password needed; the camera recognizes you.
- **Join classes** by entering a subject code, scanning a QR code, or clicking a share link.
- **Track attendance** per subject (Present count vs. Total classes).
- **Unenroll** from subjects.

---

## How It Works

SnapClass turns a face or a voice into a numeric **embedding** (a fixed-length vector) at registration time and stores it in the database. At attendance time it computes embeddings for the people in a photo/recording and matches them against the stored embeddings.

### Face Recognition Pipeline

Implemented in [pipeline/face_pipeline.py](pipeline/face_pipeline.py) using `dlib` + `face_recognition_models` + `scikit-learn`.

1. **Detection** — `dlib.get_frontal_face_detector()` locates every face in the image.
2. **Embedding** — for each detected face, a 68-point shape predictor aligns the face and `dlib`'s ResNet model (`face_recognition_model_v1`) produces a **128-dimensional embedding**.
3. **Training** — embeddings of all registered students are loaded from the database and used to fit a linear **SVM classifier** (`SVC(kernel='linear', probability=True, class_weight='balanced')`). The trained model is cached with `@st.cache_resource` and retrained whenever a new student registers.
4. **Matching** — for each face in a class photo, the SVM predicts the most likely student, then the prediction is confirmed by checking the **Euclidean distance** between embeddings against a threshold of `0.6`. Only matches under the threshold are marked present.

> Edge case: with only **one** registered student an SVM can't train (it needs ≥2 classes), so the pipeline falls back to pure distance matching.

### Voice Recognition Pipeline

Implemented in [pipeline/voice_pipeline.py](pipeline/voice_pipeline.py) using `Resemblyzer` + `librosa`.

1. **Enrollment** — a single-speaker clip is loaded at 16 kHz, preprocessed, and embedded by Resemblyzer's `VoiceEncoder` into a **256-dimensional voice fingerprint**.
2. **Roll-call splitting** — at attendance time, `librosa.effects.split()` cuts the recording on silent pauses, producing **one audio segment per student's utterance**. Segments shorter than ~0.5s (coughs/noise) are skipped.
3. **Matching** — each segment is embedded and compared to every enrolled student's stored fingerprint via **cosine similarity** (dot product). The closest match above a threshold of `0.35` is marked present; a student is never counted twice.
4. **Transparency** — a "Voice matching details" expander shows the similarity score computed for every segment so you can see exactly why each match did or didn't clear the bar.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend / App** | Streamlit |
| **Backend / DB** | Supabase (PostgreSQL) via `supabase-py` |
| **Auth (teachers)** | `bcrypt` password hashing |
| **Auth (students)** | Face ID (face recognition) |
| **Face recognition** | `dlib` (`dlib-bin`), `face_recognition_models`, `scikit-learn` (SVM) |
| **Voice recognition** | `Resemblyzer`, `librosa`, `webrtcvad`, `torch` |
| **Image / Data** | `Pillow`, `NumPy`, `pandas` |
| **QR codes** | `segno` |
| **Runtime** | Python 3.10 |

---

## Architecture & Project Structure

```
AI_Attendance_Marking_system/
├── app.py                          # Entry point: routing + join-link handling
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Pins Python 3.10 (for Streamlit Cloud)
├── .gitignore
│
├── database/
│   ├── config.py                   # Supabase client (reads secrets)
│   └── database.py                 # All DB queries (teachers, students,
│                                   #   subjects, enrollment, attendance)
│
├── pipeline/
│   ├── face_pipeline.py            # Face detection, embedding, SVM matching
│   └── voice_pipeline.py           # Voice embedding, roll-call splitting, matching
│
└── src/
    ├── screen/
    │   ├── home_screen.py          # Landing page (Student / Teacher choice)
    │   ├── teacher_screen.py       # Teacher login/register + full dashboard
    │   └── student_screen.py       # Student Face-ID login/register + dashboard
    │
    ├── components/
    │   ├── add_photo.py            # Photo capture/upload dialog (face attendance)
    │   ├── voice_attendance.py     # Roll-call audio dialog (voice attendance)
    │   ├── create_new_subject.py   # Create-subject dialog
    │   ├── enroll_in_subject.py    # Join-by-code dialog (student)
    │   ├── auto_enroll_subject.py  # Join-via-QR/link dialog (student)
    │   ├── share_subject.py        # QR code + share link generator
    │   ├── show_attendance_results.py # Confirm/discard results dialog
    │   ├── subject_card.py         # Reusable subject card UI
    │   ├── header.py / footer.py   # Shared chrome
    │
    └── ui/
        └── base_layout.py          # Shared CSS / layout styling
```

### Application Flow

`app.py` is the single entry point. It:
1. Reads the `?join_subject=<id>` URL parameter (set by share links / QR codes) and routes the visitor into the student flow, opening the auto-enroll dialog when they're logged in.
2. Routes to the correct screen based on `st.session_state['login_type']` — `home`, `teacher`, or `student`.

State is held entirely in Streamlit's `st.session_state` (login type, logged-in flag, role, current user details, captured photos, attendance results, etc.).

---

## Database Schema

SnapClass uses a Supabase (PostgreSQL) database with five tables. All `*_id` primary keys are auto-generated `int8` identity columns.

#### `teachers`
| Column | Type | Notes |
|--------|------|-------|
| `teacher_id` | `int8` | Primary key |
| `username` | `text` | Unique (indexed) |
| `password` | `text` | `bcrypt` hash |
| `name` | `text` | Display name |

#### `students`
| Column | Type | Notes |
|--------|------|-------|
| `student_id` | `int8` | Primary key |
| `name` | `text` | Full name |
| `face_embedding` | `jsonb` | 128-d face embedding (list of floats) |
| `voice_embedding` | `jsonb` | 256-d voice fingerprint (nullable — only if voice was registered) |

#### `subjects`
| Column | Type | Notes |
|--------|------|-------|
| `subject_id` | `int8` | Primary key |
| `subject_code` | `text` | e.g. `CS101` |
| `name` | `text` | Subject name |
| `section` | `text` | e.g. `A` |
| `teacher_id` | `int8` | → `teachers.teacher_id` |

#### `subject_student` (enrollment join table)
| Column | Type | Notes |
|--------|------|-------|
| `subject_id` | `int8` | → `subjects.subject_id` |
| `student_id` | `int8` | → `students.student_id` |

#### `attendance`
| Column | Type | Notes |
|--------|------|-------|
| `id` | `int8` | Primary key |
| `timestamp` | — | Session time (`YYYY-MM-DD HH:MM:SS`) |
| `subject_id` | `int8` | → `subjects.subject_id` |
| `student_id` | `int8` | → `students.student_id` |
| `is_present` | `bool` | Present/absent for this session |

A "session" is one batch of `attendance` rows that share the same `timestamp`, written when the teacher confirms a marking run. Embeddings are stored as `jsonb` (the pipelines serialize NumPy vectors to plain lists before insert).

---

## Getting Started

### Prerequisites

- **Python 3.10** (pinned in [runtime.txt](runtime.txt); `dlib` wheels and other deps are most reliable here).
- A free **[Supabase](https://supabase.com/)** project.
- On Windows, the `dlib-bin` package ships prebuilt wheels so you do **not** need a C++ compiler.

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ajithreddy3/SnapClass---AI-Attendance-Marking-System.git
cd SnapClass---AI-Attendance-Marking-System

# 2. Create and activate a virtual environment
python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

> The first install also pulls `face_recognition_models` directly from GitHub and downloads the `torch` runtime, so it may take a few minutes.

### Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com/).
2. Create the five tables exactly as described in [Database Schema](#database-schema) — `teachers`, `students`, `subjects`, `subject_student`, and `attendance` — with the listed column types and foreign keys. (`face_embedding` / `voice_embedding` must be `jsonb`.)
3. From **Project Settings → API**, copy your **Project URL** and **anon/public API key**.

### Configuring Secrets

The Supabase client in [database/config.py](database/config.py) reads credentials from Streamlit secrets. Create a file at `.streamlit/secrets.toml` (this path is git-ignored — **never commit it**):

```toml
SUPA_BASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY  = "your-supabase-anon-key"
```

### Running the App

```bash
streamlit run app.py
```

Streamlit opens the app in your browser (default: `http://localhost:8501`). Camera and microphone inputs require granting browser permissions.

---

## User Guide

### For Teachers

1. **Register / Log in** — from the home page choose *Teacher Portal*, then register a profile (username, full name, password) and log in.
2. **Create a subject** — go to **Manage Subjects → Add New Subject** and enter a name, code, and section.
3. **Share the class** — click **Share Class** on a subject card to show a QR code and join link. Students scan/open it to enroll.
4. **Take attendance:**
   - **By photo:** **Attendance Marking** tab → select the subject → **Take Attendance** → capture/upload one or more class photos → **Mark Attendance**. Review the Present/Absent table, then **Confirm**.
   - **By voice:** click **Voice Attendance** → record or upload a clip of students saying *"present"* one at a time → **Mark Attendance** → review and **Confirm**.
5. **Review & export** — the **Attendance Records** tab lists every session (date, time, subject, present/total), supports filtering by subject, and exports to **CSV**.

### For Students

1. **Register** — choose *Student Portal*. On first login your face won't be recognized, so you'll be sent to registration: enter your name, capture your face, and optionally record yourself saying *"present"* to enable voice attendance.
2. **Log in with Face ID** — return to the Student Portal and capture your face; the system recognizes you and opens your dashboard.
3. **Join a class** — click **Enroll in a new subject** and enter the subject code, **or** scan the teacher's QR code / open the share link to auto-enroll.
4. **Track attendance** — each subject card shows your Present count vs. total classes. Use **Unenroll** to leave a class.

---

## Deployment

The project is configured for **[Streamlit Community Cloud](https://streamlit.io/cloud)**:

- [runtime.txt](runtime.txt) pins the Python version to `3.10`.
- [requirements.txt](requirements.txt) lists all dependencies (with `setuptools<70.0.0` pinned to avoid legacy install breakage).
- Add `SUPA_BASE_URL` and `SUPABASE_KEY` in the app's **Secrets** settings on Streamlit Cloud (same keys as `secrets.toml`).
- The share-link domain is set in [src/components/share_subject.py](src/components/share_subject.py) (`app_domain`). Update it to match your deployed app's URL so QR codes/links point to the right place.

---

## Notes & Limitations

- **Recognition thresholds** (face distance `0.6`, voice similarity `0.35`) are tuned heuristically — adjust them in the pipeline files for stricter or looser matching.
- Face attendance works best with **clear, well-lit, front-facing** photos. Registration requires exactly one clearly detected face.
- Voice roll-call relies on **distinct pauses** between speakers; overlapping voices reduce accuracy.
- Biometric embeddings (not raw photos/audio) are stored, but you are still handling biometric data — ensure you have consent and comply with applicable privacy regulations before deploying.
- The face model is cached and retrained on registration; with a large number of students, training/matching latency will grow.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
