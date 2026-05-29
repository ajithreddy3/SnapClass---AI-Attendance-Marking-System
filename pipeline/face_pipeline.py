from sklearn.svm import SVC
import numpy as np
import dlib
import face_recognition_models
from database.database import get_all_students
import streamlit as st
@st.cache_resource
def face_recognition_pipeline():

    face_detector = dlib.get_frontal_face_detector()
    face_recognition_model = dlib.shape_predictor(face_recognition_models.pose_predictor_model_location())
    facerec = dlib.face_recognition_model_v1(face_recognition_models.face_recognition_model_location())

    return face_detector, face_recognition_model, facerec

def extract_face_embeddings(image):
    face_detector, face_recognition_model, facerec = face_recognition_pipeline()
    detected_faces = face_detector(image, 1)

    embeddings = []
    for face in detected_faces:
        shape = face_recognition_model(image, face)
        face_descriptor = facerec.compute_face_descriptor(image, shape , 1)
        embeddings.append(np.array(face_descriptor))
    return embeddings

@st.cache_resource
def train_face_recognition_model():
    students = get_all_students()
    X = []
    y = []

    if not students:
        st.warning("No student data found. Please add students to the database.")
        return None
    for student in students:
        embeddings = student.get("face_embedding")

        if embeddings:
            X.append(np.array(embeddings))
            y.append(student.get('student_id'))
    if not X :
        return 0 
    model = SVC(kernel='linear', probability=True , class_weight='balanced')
    # An SVM needs at least 2 classes to train. With only one registered student,
    # attendance_marking_pipeline matches by distance instead, so skip fitting.
    if len(set(y)) > 1:
        try :
            model.fit(X, y)
        except Exception as e:
            st.error(f"Error training face recognition model: {e}")

    return {"model": model , "X" : X , "y" : y}


def update_model():
    st.cache_resource.clear()
    model_data = train_face_recognition_model()
    return bool(model_data)

def attendance_marking_pipeline(image):
    model_data = train_face_recognition_model()
    embeddings = extract_face_embeddings(image)
    students = {}
    if not model_data:
        return students , [] , len(embeddings)
    model = model_data["model"] 
    X_train = model_data["X"]
    y_train = model_data["y"]
    for embedding in embeddings:
        if len(y_train) == 1:
            student_id = y_train[0]
        else:
            student_id = model.predict([embedding])[0]
        
        student_embeddings = X_train[y_train.index(student_id)]
        best_match_score = np.linalg.norm(student_embeddings - embedding)
        threshold = 0.6
        if best_match_score < threshold:
            students[student_id] = True 
        
    return students , y_train , len(embeddings)