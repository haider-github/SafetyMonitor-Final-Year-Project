from ultralytics import YOLO
import cv2

# Your exact class names from the model
GEAR_CLASSES = ["glasses", "gloves", "helmet", "mask", "vest"]
REQUIRED_GEAR = ["helmet", "vest", "glasses", "gloves", "mask"]

# Colors for drawing boxes (BGR format)
COLORS = {
    "person": (255, 165, 0),
    "helmet": (0, 255, 0),
    "vest": (0, 255, 0),
    "glasses": (0, 255, 0),
    "gloves": (0, 255, 0),
    "mask": (0, 255, 0),
    "PPE": (0, 200, 255),
}

model = YOLO("model/best.pt")

def detect_ppe(frame):
    results = model(frame, conf=0.4, verbose=False)
    detected_classes = []

    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            conf = float(box.conf[0])
            detected_classes.append(class_name)

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = COLORS.get(class_name, (0, 255, 0))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{class_name} {conf:.0%}"
            cv2.putText(frame, label, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    # Only check for missing gear if a person is in the frame
    missing_gear = []
    if "person" in detected_classes or "PPE" in detected_classes:
        missing_gear = [g for g in REQUIRED_GEAR if g not in detected_classes]

    return frame, detected_classes, missing_gear