import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch.nn.functional as F
import torch.nn as nn

# -----------------------
# CONFIG
# -----------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 128
NUM_BUCKETS = 6
THRESHOLD = 0.7

# -----------------------
# TRANSFORM
# -----------------------
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.5]*3, [0.5]*3)
])

# -----------------------
# GENERATOR (same as training)
# -----------------------
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

# -----------------------
# LOAD MODELS
# -----------------------
G = Generator().to(DEVICE)
checkpoint = torch.load("epoch_30.pt", map_location=DEVICE)
G.load_state_dict(checkpoint["G"])
G.eval()

mtcnn = MTCNN(image_size=IMG_SIZE)
face_net = InceptionResnetV1(pretrained='vggface2').eval().to(DEVICE)

print("Models loaded successfully")

# -----------------------
# GUARDIAN INPUT
# -----------------------
guardian_img = Image.open("win.jpg").convert("RGB")
guardian_tensor = transform(guardian_img).unsqueeze(0).to(DEVICE)

# Generate age-progressed faces
generated_embeddings = []

with torch.no_grad():
    for bucket in range(NUM_BUCKETS):
        age_tensor = torch.tensor([bucket]).to(DEVICE)
        gen_face = G(guardian_tensor, age_tensor)
        emb = face_net(gen_face)
        emb = emb / emb.norm(dim=1, keepdim=True)
        generated_embeddings.append(emb)

print("Age-progressed identity embeddings ready")

# -----------------------
# CCTV (WEBCAM)
# -----------------------
cap = cv2.VideoCapture(0)

print("CCTV started. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face = mtcnn(rgb)

    best_similarity = -1.0  # track best match

    if face is not None:
        face = face.unsqueeze(0).to(DEVICE)
        emb = face_net(face)
        emb = emb / emb.norm(dim=1, keepdim=True)
        print(emb)

        # Compare with ALL age-progressed embeddings
        for gen_emb in generated_embeddings:
            sim = F.cosine_similarity(emb, gen_emb).item()
            best_similarity = max(best_similarity, sim)
            # print(sim)
        # print(best_similarity)
        # Convert similarity to percentage
        match_percentage = max(0, (best_similarity + 1) / 2) * 100

        # Display match percentage always
        cv2.putText(
            frame,
            f"Match: {match_percentage:.2f}%",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Alert condition
        if best_similarity > THRESHOLD:
            cv2.putText(
                frame,
                "ALERT: MATCH FOUND",
                (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                3
            )

    cv2.imshow("CCTV Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
