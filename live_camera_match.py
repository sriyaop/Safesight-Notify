import cv2
import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine

# ---------------- CONFIG ----------------
META_CSV = "data/cleaned/metadata.csv"
MATCH_THRESHOLD = 0.75   # 75% similarity threshold
CAMERA_INDEX = 0         # change to 1 if external webcam
# ----------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load models
mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

# Load metadata & embeddings
df = pd.read_csv(META_CSV)

db_embeddings = []
db_records = []

for _, row in df.iterrows():
    emb_path = row.get("embedding_path", "")
    if isinstance(emb_path, str) and emb_path.strip() != "":
        db_embeddings.append(np.load(emb_path))
        db_records.append(row)

print(f"Loaded {len(db_embeddings)} embeddings from database")

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("❌ Could not open camera")
    exit()

print("📷 Camera started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect face
    face = mtcnn(img_rgb)

    label = "NO FACE"
    color = (0, 0, 255)

    if face is not None:
        face = face.unsqueeze(0).to(device)

        with torch.no_grad():
            query_emb = resnet(face).cpu().numpy().flatten()

        best_score = 0
        best_match = None

        for db_emb, record in zip(db_embeddings, db_records):
            score = 1 - cosine(query_emb, db_emb)
            if score > best_score:
                best_score = score
                best_match = record

        match_percent = best_score * 100

        if best_score >= MATCH_THRESHOLD:
            label = f"MATCH: {best_match['child_name']} ({match_percent:.1f}%)"
            color = (0, 255, 0)
        else:
            label = f"NO MATCH ({match_percent:.1f}%)"
            color = (0, 0, 255)

    # Draw result
    cv2.putText(frame, label, (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("SafeSightNotify - Live Face Matching", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

