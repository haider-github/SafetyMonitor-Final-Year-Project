import cv2
import numpy as np
import os
from database import get_all_workers

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    RECOGNIZER_AVAILABLE = True
except Exception:
    RECOGNIZER_AVAILABLE = False
    print("Face recognizer not available — showing camera without recognition.")

label_map = {}
is_trained = False


def train_recognizer():
    global label_map, is_trained

    if not RECOGNIZER_AVAILABLE:
        return False

    workers  = get_all_workers()
    faces    = []
    labels   = []
    label_map = {}
    label_id  = 0

    for worker in workers:
        worker_id  = worker[1]
        name       = worker[2]
        image_path = worker[6]

        if not image_path or not os.path.exists(image_path):
            continue

        img = cv2.imread(image_path)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detected = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
        )

        for (x, y, w, h) in detected:
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
            faces.append(face_roi)
            labels.append(label_id)

        label_map[label_id] = {
            "worker_id":  worker_id,
            "name":       name,
            "phone":      worker[3] or "N/A",
            "department": worker[4] or "N/A",
            "location":   worker[5] or "N/A",
        }
        label_id += 1

    if len(faces) == 0:
        print("No worker photos found for training.")
        is_trained = False
        return False

    recognizer.train(faces, np.array(labels))
    is_trained = True
    print(f"Face recognizer trained on {len(faces)} face(s) "
          f"from {label_id} worker(s).")
    return True


def recognize_faces(frame):
    """
    Detect and recognize faces in frame.
    Returns annotated frame and list of recognized workers.
    """
    if frame is None:
        return frame, []

    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    except Exception:
        return frame, []

    try:
        detected = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )
    except Exception:
        return frame, []

    recognized_workers = []

    for (x, y, w, h) in detected:
        try:
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))

            if is_trained and RECOGNIZER_AVAILABLE:
                label, confidence = recognizer.predict(face_roi)

                if confidence < 100 and label in label_map:
                    worker = label_map[label]
                    name   = worker["name"]
                    dept   = worker["department"]
                    wid    = worker["worker_id"]
                    color  = (0, 255, 0)
                    recognized_workers.append(worker)

                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    tag   = f"{name} ({wid})"
                    tw    = len(tag) * 11
                    cv2.rectangle(frame, (x, y-45), (x+tw, y), (0, 180, 0), -1)
                    cv2.putText(frame, tag, (x+4, y-26),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (255, 255, 255), 2)
                    cv2.putText(frame, dept, (x+4, y-8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                                (255, 255, 255), 1)
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h),
                                  (0, 0, 255), 2)
                    cv2.rectangle(frame, (x, y-30), (x+130, y),
                                  (0, 0, 180), -1)
                    cv2.putText(frame, "UNKNOWN", (x+4, y-8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (255, 255, 255), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h),
                              (200, 200, 0), 2)

        except Exception as e:
            print(f"Face recognition error: {e}")
            continue

    return frame, recognized_workers