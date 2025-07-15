import cv2
import numpy as np
from insightface.model_zoo import ArcFaceONNX
from insightface.app import FaceAnalysis
from ultralytics import YOLO


def align_face_with_kps(img, kps, output_size=(112, 112)):
    if kps is None or len(kps) != 5:
        print("❌ Invalid keypoints for alignment")
        return None

    # Standard 5-point reference from ArcFace
    src = np.array([
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041]
    ], dtype=np.float32)

    dst = np.array(kps, dtype=np.float32)

    # Estimate affine transform
    M, _ = cv2.estimateAffinePartial2D(dst, src, method=cv2.LMEDS)

    if M is None:
        print("❌ Alignment matrix calculation failed.")
        return None

    aligned_face = cv2.warpAffine(img, M, output_size, borderValue=0.0)
    return aligned_face


# preprocess.py or alignment.py


# Init once globally (move this outside function)
face_detector = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark"])
face_detector.prepare(ctx_id=-1)

def align_and_crop_face(frame):
    faces = face_detector.get(frame)
    if not faces:
        return None

    face = faces[0]
    aligned = align_face_with_kps(frame, face.kps)

    if aligned is None or aligned.size == 0:
        # Fallback: use bounding box
        bbox = face.bbox.astype(int)
        x1 = max(bbox[0], 0)
        y1 = max(bbox[1], 0)
        x2 = min(bbox[2], frame.shape[1])
        y2 = min(bbox[3], frame.shape[0])
        aligned = frame[y1:y2, x1:x2]

        if aligned is None or aligned.size == 0:
            return None

    resized = cv2.resize(aligned, (112, 112))
    return resized




# Init globally
embedder = ArcFaceONNX(model_file="./models/model.onnx")
embedder.prepare(ctx_id=-1)

def get_embedding_from_frame(face_img):
    """
    face_img: 112x112 aligned image (numpy array)
    returns: 1D embedding vector
    """
    if face_img is None or face_img.shape[:2] != (112, 112):
        return None

    return embedder.get_feat(face_img)

# preprocess.py or predictor.py

def predict_identity(frame):
    from insightface.app import FaceAnalysis
    from insightface.model_zoo import ArcFaceONNX
    import numpy as np
    import cv2
    import joblib

    # Load models once (optional: make global to avoid reload)
    detector = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "landmark"])
    detector.prepare(ctx_id=-1)
    embedder = ArcFaceONNX(model_file="./models/model.onnx")
    embedder.prepare(ctx_id=-1)
    
    clf = joblib.load("./models/svm_classifier.joblib")
    le = joblib.load("./models/label_encoder.joblib")

    # Detect and align face
    faces = detector.get(frame)
    if not faces:
        return "❌ No face found"

    face = faces[0]
    aligned = align_face_with_kps(frame, face.kps)

    if aligned is None:
        return "⚠️ Could not align"

    aligned = cv2.resize(aligned, (112, 112))

    # Get embedding
    emb = embedder.get_feat(aligned)  # shape: (1, 512) or possibly (512,)

    # FIX: Reshape embedding if needed
    if len(emb.shape) == 3:
        emb = emb.reshape(-1)

    if len(emb.shape) == 1:
        emb = emb.reshape(1, -1)

    # Predict identity
    pred = clf.predict(emb)[0]
    name = le.inverse_transform([pred])[0]
    return name




#---------------------------- PPE DETECTION ------------------------


def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)




def run_yolo_on_frame(frame):
    """
    Accepts a BGR image (numpy array), runs YOLOv8 detection,
    draws bounding boxes, and returns:
    - Annotated image
    - Boxes grouped by class
    - Class name mapping
    """
    # Load model once
    model = YOLO("./models/best.pt")

    # Run prediction on frame
    results = model.predict(frame, conf=0.5, iou=0.4)
    result = results[0]

    # Extract info
    orig_img = result.orig_img.copy()
    boxes = result.boxes.xywh.cpu().numpy()        # [x_center, y_center, w, h]
    confidences = result.boxes.conf.cpu().numpy()
    class_ids = result.boxes.cls.cpu().numpy().astype(int)
    names = result.names

    print(f"Number of boxes detected: {len(boxes)}")
    print("Class IDs:", class_ids)
    print("Class Names:", names)

    # Group boxes by class
    boxes_by_class = {}

    for i, box in enumerate(boxes):
        x_center, y_center, width, height = box
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)
        class_name = names[class_ids[i]]

        # Draw box
        color = (0, 255, 0)
        cv2.rectangle(orig_img, (x1, y1), (x2, y2), color, 2)

        # Label
        label = f"{class_name} {confidences[i]:.2f}"
        cv2.putText(orig_img, label, (x1, y1 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Save box
        boxes_by_class.setdefault(class_name, []).append((x1, y1, x2, y2))

    return orig_img, boxes_by_class, names


def check_ppe_compliance(image, boxes_by_class):
    required_ppe = ['Mask', 'Gloves', 'Coverall', 'Face_Shield', 'Goggles']
    persons = boxes_by_class.get("person", [])
    compliance_summary = []

    def is_center_inside(person_box, ppe_box):
        # PPE center point
        cx = (ppe_box[0] + ppe_box[2]) // 2
        cy = (ppe_box[1] + ppe_box[3]) // 2
        # Person box
        px1, py1, px2, py2 = person_box
        return px1 <= cx <= px2 and py1 <= cy <= py2

    for idx, person_box in enumerate(persons, 1):
        px1, py1, px2, py2 = person_box
        compliant = {}
        all_good = True

        for ppe in required_ppe:
            matched = False
            for ppe_box in boxes_by_class.get(ppe, []):
                if is_center_inside(person_box, ppe_box):
                    matched = True
                    break
            compliant[ppe] = matched
            if not matched:
                all_good = False

        # Draw bounding box around person
        color = (0, 255, 0) if all_good else (0, 0, 255)
        cv2.rectangle(image, (px1, py1), (px2, py2), color, 3)
        label = f"Person {idx} - {'OK' if all_good else 'PPE Missing'}"
        cv2.putText(image, label, (px1, py1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Print result
        print(f"🧍 Person {idx} Compliance:")
        for item in required_ppe:
            print(f"   - {item}: {'✅' if compliant[item] else '❌'}")
        print()

        compliance_summary.append((idx, compliant))

    return image, compliance_summary






