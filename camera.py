import cv2
import time
import os
import threading
from detector import detect_ppe
from database import log_violation
from face_recognition_module import recognize_faces, train_recognizer

try:
    from email_alerts import send_violation_email
    EMAIL_ENABLED = True
    print("Email alerts enabled.")
except Exception:
    EMAIL_ENABLED = False
    print("Email alerts disabled. Fill in email_alerts.py to enable.")

LOG_INTERVAL = 30


class VideoStream:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        self.last_log_time   = 0
        self.current_missing = []
        self.active_worker   = None
        train_recognizer()

    def retrain(self):
        train_recognizer()

    def generate_frames(self):
        while True:
            success, frame = self.cap.read()
            if not success:
                break

            # Step 1 — Face recognition
            frame, recognized_workers = recognize_faces(frame)

            # Step 2 — PPE detection
            frame, detected, missing = detect_ppe(frame)
            self.current_missing = missing

            h, w = frame.shape[:2]

            # Step 3 — Violation bar
            if self.current_missing:
                missing_text = "VIOLATION: Missing " + ", ".join(self.current_missing)
                cv2.rectangle(frame, (0, 0), (w, 45), (0, 0, 180), -1)
                cv2.putText(frame, missing_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                now = time.time()
                if now - self.last_log_time > LOG_INTERVAL:
                    snapshot = self.save_snapshot(frame)

                    if recognized_workers:
                        for worker in recognized_workers:
                            log_violation(
                                worker["worker_id"],
                                ", ".join(self.current_missing),
                                snapshot
                            )
                            if EMAIL_ENABLED:
                                threading.Thread(
                                    target=send_violation_email,
                                    args=(
                                        worker["name"],
                                        worker["worker_id"],
                                        worker["department"],
                                        worker["phone"],
                                        ", ".join(self.current_missing),
                                        snapshot
                                    ),
                                    daemon=True
                                ).start()
                    else:
                        log_violation(
                            "UNKNOWN",
                            ", ".join(self.current_missing),
                            snapshot
                        )
                        if EMAIL_ENABLED:
                            threading.Thread(
                                target=send_violation_email,
                                args=(
                                    "Unknown Worker",
                                    "UNKNOWN",
                                    "—", "—",
                                    ", ".join(self.current_missing),
                                    snapshot
                                ),
                                daemon=True
                            ).start()

                    self.last_log_time = now

            else:
                cv2.rectangle(frame, (0, 0), (300, 45), (0, 130, 0), -1)
                cv2.putText(frame, "ALL GEAR OK - SAFE", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    def save_snapshot(self, frame):
        os.makedirs("static/snapshots", exist_ok=True)
        filename = f"static/snapshots/violation_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)
        return filename

    def release(self):
        self.cap.release()


class MultiCameraStream:
    def __init__(self, sources):
        self.streams = {
            str(i): VideoStream(source=s)
            for i, s in enumerate(sources)
        }

    def get_stream(self, cam_id):
        return self.streams.get(str(cam_id))

    def release_all(self):
        for s in self.streams.values():
            s.release()