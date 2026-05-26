from ultralytics import YOLO

model = YOLO("model/best.pt")

print("=" * 40)
print("YOUR MODEL CLASS NAMES:")
print("=" * 40)
for i, name in model.names.items():
    print(f"  Class {i}: {name}")
print("=" * 40)
print("Model loaded successfully!")