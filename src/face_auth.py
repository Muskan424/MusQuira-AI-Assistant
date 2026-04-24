
"""
👤 Face Recognition Login for MusQuira
Uses OpenCV haar cascades — no extra models needed.
"""

import os, cv2, pickle, time, numpy as np
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import FACE_DATA_DIR

ENCODINGS_FILE = os.path.join(FACE_DATA_DIR, "encodings.pkl")
CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def ensure_dir():
    os.makedirs(FACE_DATA_DIR, exist_ok=True)


def _get_face_crop(frame):
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = CASCADE.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return None
    x, y, w, h = faces[0]
    crop = cv2.resize(gray[y:y+h, x:x+w], (128, 128))
    return crop.flatten().astype("float32")


def enroll_face(username: str, status_cb=None) -> bool:
    ensure_dir()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        if status_cb: status_cb("Camera not accessible.")
        return False
    if status_cb: status_cb(f"Enrolling '{username}'… Look at camera.")
    samples, attempts = [], 0
    while len(samples) < 30 and attempts < 150:
        ret, frame = cap.read()
        if not ret:
            attempts += 1
            continue
        vec = _get_face_crop(frame)
        if vec is not None:
            samples.append(vec)
        attempts += 1
        time.sleep(0.05)
    cap.release()
    if len(samples) < 5:
        if status_cb: status_cb("Not enough samples. Try better lighting.")
        return False
    data = {}
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
    data[username] = np.mean(samples, axis=0)
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)
    if status_cb: status_cb(f"✅ Face enrolled for {username}!")
    return True


def recognize_face(status_cb=None, timeout=20) -> str | None:
    if not os.path.exists(ENCODINGS_FILE):
        return "Guest"
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    if not data:
        return "Guest"
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        if status_cb: status_cb("Camera unavailable.")
        return "Guest"
    if status_cb: status_cb("👁 Scanning face… look at camera.")
    start  = time.time()
    votes  = {}
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if not ret:
            continue
        vec = _get_face_crop(frame)
        if vec is None:
            continue
        best_name, best_dist = None, float("inf")
        for name, stored in data.items():
            dist = float(np.linalg.norm(vec - stored))
            if dist < best_dist:
                best_dist, best_name = dist, name
        if best_dist < 8000:
            votes[best_name] = votes.get(best_name, 0) + 1
            if votes[best_name] >= 5:
                cap.release()
                if status_cb: status_cb(f"✅ Identity confirmed: {best_name}")
                return best_name
    cap.release()
    if status_cb: status_cb("Face not recognized.")
    return None


def list_enrolled() -> list:
    if not os.path.exists(ENCODINGS_FILE):
        return []
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    return list(data.keys())


def delete_enrollment(username: str) -> bool:
    if not os.path.exists(ENCODINGS_FILE):
        return False
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    if username in data:
        del data[username]
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(data, f)
        return True
    return False
