import cv2
import torch
import numpy as np
from PIL import Image
import torch.nn.functional as F
import torch.nn as nn
import os

from facenet_pytorch import MTCNN, InceptionResnetV1


# =========================================================
# CONFIG
# =========================================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 128
NUM_BUCKETS = 6
THRESHOLD = 0.55

CHILDREN_FOLDER = "missing_children"  # put images here
CHECKPOINT = "epoch_30.pt"


# =========================================================
# AGE PROGRESSION GENERATOR
# =========================================================
class Generator(nn.Module):
    def __init__(self):
        super().__init__()
        self.age_embed = nn.Embedding(NUM_BUCKETS, NUM_BUCKETS)

        self.model = nn.Sequential(
            nn.Conv2d(3 + NUM_BUCKETS, 64, 4, 2, 1),
            nn.ReLU(),

            nn.Conv2d(64, 128, 4, 2, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.Conv2d(128, 256, 4, 2, 1),
            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.ConvTranspose2d(256, 128, 4, 2, 1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.ConvTranspose2d(128, 64, 4, 2, 1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.ConvTranspose2d(64, 3, 4, 2, 1),
            nn.Tanh()
        )

    def forward(self, x, age_bucket):
        age = self.age_embed(age_bucket)
        age = age.unsqueeze(2).unsqueeze(3)
        age = age.expand(-1, -1, IMG_SIZE, IMG_SIZE)

        x = torch.cat([x, age], dim=1)
        return self.model(x)


# =========================================================
# LOAD MODELS
# =========================================================
print("Loading models...")

G = Generator().to(DEVICE)
checkpoint = torch.load(CHECKPOINT, map_location=DEVICE)
G.load_state_dict(checkpoint["G"])
G.eval()

# Face detector + embedder
mtcnn = MTCNN(
    image_size=IMG_SIZE,
    keep_all=True,
    device=DEVICE
)
face_net = InceptionResnetV1(pretrained='vggface2').eval().to(DEVICE)  

print("✅ Models ready")


# =========================================================
# BUILD DATABASE
# =========================================================
database = {}

print("\nBuilding missing children database...")

for file in os.listdir(CHILDREN_FOLDER):

    path = os.path.join(CHILDREN_FOLDER, file)

    try:
        img = Image.open(path).convert("RGB")
    except:
        continue

    aligned = mtcnn(img)

    if aligned is None:
        print(f"⚠️ No face in {file}")
        continue

    # ---------- SHAPE FIX ----------
    if aligned.ndim == 3:
        tensor = aligned.unsqueeze(0)
    else:
        tensor = aligned[0].unsqueeze(0)

    tensor = tensor.to(DEVICE)

    refs = []

    with torch.no_grad():

        # ORIGINAL embedding
        emb = face_net(tensor)
        emb = emb / emb.norm(dim=1, keepdim=True)
        refs.append(emb)

        # AGE PROGRESSION embeddings
        for bucket in range(NUM_BUCKETS):
            age = torch.tensor([bucket]).to(DEVICE)
            gen = G(tensor, age)

            emb = face_net(gen)
            emb = emb / emb.norm(dim=1, keepdim=True)
            refs.append(emb)

    database[file] = refs
    print(f"Registered → {file}")

print(f"\n✅ Total children registered: {len(database)}")


# =========================================================
# CCTV LOOP
# =========================================================
cap = cv2.VideoCapture(0)
print("\n🎥 CCTV Running — Press Q to quit\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    boxes, _ = mtcnn.detect(rgb)

    if boxes is not None:

        faces = mtcnn(rgb)

        for box, face in zip(boxes, faces):

            x1, y1, x2, y2 = map(int, box)
            if face.ndim == 3:
                face = face.unsqueeze(0)
            else:
                face = face[0].unsqueeze(0)

            face = face.to(DEVICE)

            with torch.no_grad():
                emb = face_net(face)
                emb = emb / emb.norm(dim=1, keepdim=True)

            best_child = None
            best_sim = -1

            # Compare with database
            for child, refs in database.items():
                for ref in refs:
                    sim = F.cosine_similarity(emb, ref).item()
                    if sim > best_sim:
                        best_sim = sim
                        best_child = child

            # Convert similarity to readable %
            MIN_SIM = 0.3
            MAX_SIM = 0.8

            sim_clamped = max(MIN_SIM, min(best_sim, MAX_SIM))
            percent = (sim_clamped - MIN_SIM) / (MAX_SIM - MIN_SIM) * 100

            # Label decision
            if best_sim > THRESHOLD:
                label = f"{best_child}  {percent:.1f}%"
                color = (0, 0, 255)
            else:
                label = f"Unknown  {percent:.1f}%"
                color = (0, 255, 0)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

    cv2.imshow("Many-to-Many Missing Child Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()