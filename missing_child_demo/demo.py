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
THRESHOLD = 0.55

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

# # -----------------------
# # CCTV (WEBCAM)
# # -----------------------
# cap = cv2.VideoCapture(0)

# print("CCTV started. Press Q to quit.")

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     face = mtcnn(rgb)

#     if face is not None:
#         face = face.unsqueeze(0).to(DEVICE)
#         emb = face_net(face)
#         emb = emb / emb.norm(dim=1, keepdim=True)

#         for gen_emb in generated_embeddings:
#             sim = F.cosine_similarity(emb, gen_emb).item()
#             if sim > THRESHOLD:
#                 cv2.putText(
#                     frame,
#                     f"ALERT! MATCH FOUND ({sim:.2f})",
#                     (30, 50),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     1,
#                     (0, 0, 255),
#                     3
#                 )
#                 break

#     cv2.imshow("CCTV Feed", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()

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

    best_similarity = 0.0  # track best match

    if face is not None:
        face = face.unsqueeze(0).to(DEVICE)
        emb = face_net(face)
        emb = emb / emb.norm(dim=1, keepdim=True)

        # Compare with ALL age-progressed embeddings
        for gen_emb in generated_embeddings:
            sim = F.cosine_similarity(emb, gen_emb).item()
            best_similarity = max(best_similarity, sim)

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


# import cv2
# import torch
# import numpy as np
# from PIL import Image
# from torchvision import transforms
# import torch.nn as nn
# import torch.nn.functional as F
# from facenet_pytorch import MTCNN, InceptionResnetV1

# # =====================================================
# # CONFIG
# # =====================================================
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# IMG_SIZE = 128
# NUM_BUCKETS = 6
# THRESHOLD = 0.55
# GUARDIAN_AGE = 7

# # =====================================================
# # AGE BUCKET
# # =====================================================
# def age_to_bucket(age):
#     if age <= 2: return 0
#     elif age <= 5: return 1
#     elif age <= 8: return 2
#     elif age <= 12: return 3
#     elif age <= 16: return 4
#     else: return 5

# START_BUCKET = age_to_bucket(GUARDIAN_AGE)

# # =====================================================
# # SIMILARITY → %
# # =====================================================
# def similarity_to_percent(sim):
#     sim = max(0.3, min(sim, 0.8))
#     return ((sim - 0.3) / (0.8 - 0.3)) * 100

# # =====================================================
# # TRANSFORM
# # =====================================================
# transform = transforms.Compose([
#     transforms.Resize((IMG_SIZE, IMG_SIZE)),
#     transforms.ToTensor(),
#     transforms.Normalize([0.5]*3, [0.5]*3)
# ])

# # =====================================================
# # GENERATOR
# # =====================================================
# class Generator(nn.Module):
#     def __init__(self):
#         super().__init__()
#         self.age_embed = nn.Embedding(NUM_BUCKETS, NUM_BUCKETS)
#         self.model = nn.Sequential(
#             nn.Conv2d(3 + NUM_BUCKETS, 64, 4, 2, 1),
#             nn.ReLU(),
#             nn.Conv2d(64, 128, 4, 2, 1),
#             nn.BatchNorm2d(128),
#             nn.ReLU(),
#             nn.Conv2d(128, 256, 4, 2, 1),
#             nn.BatchNorm2d(256),
#             nn.ReLU(),
#             nn.ConvTranspose2d(256, 128, 4, 2, 1),
#             nn.BatchNorm2d(128),
#             nn.ReLU(),
#             nn.ConvTranspose2d(128, 64, 4, 2, 1),
#             nn.BatchNorm2d(64),
#             nn.ReLU(),
#             nn.ConvTranspose2d(64, 3, 4, 2, 1),
#             nn.Tanh()
#         )

#     def forward(self, x, age_bucket):
#         age = self.age_embed(age_bucket)
#         age = age.unsqueeze(2).unsqueeze(3)
#         age = age.expand(-1, -1, IMG_SIZE, IMG_SIZE)
#         x = torch.cat([x, age], dim=1)
#         return self.model(x)

# # =====================================================
# # LOAD MODELS
# # =====================================================
# G = Generator().to(DEVICE)
# ckpt = torch.load("epoch_30.pt", map_location=DEVICE)
# G.load_state_dict(ckpt["G"])
# G.eval()

# print("✅ Generator loaded")

# mtcnn = MTCNN(image_size=IMG_SIZE, device=DEVICE)

# face_net = InceptionResnetV1(
#     pretrained='vggface2'
# ).eval().to(DEVICE)

# print("✅ ArcFace-style embedding model loaded")

# # =====================================================
# # GUARDIAN IMAGE
# # =====================================================
# guardian_img = Image.open("child.jpg").convert("RGB")
# guardian_tensor = transform(guardian_img).unsqueeze(0).to(DEVICE)

# # =====================================================
# # GENERATE AGE-PROGRESSED EMBEDDINGS
# # =====================================================
# generated_embeddings = []

# with torch.no_grad():
#     for bucket in range(START_BUCKET + 1, NUM_BUCKETS):
#         age_tensor = torch.tensor([bucket]).to(DEVICE)
#         gen_face = G(guardian_tensor, age_tensor)
#         emb = face_net(gen_face)
#         emb = F.normalize(emb, dim=1)
#         generated_embeddings.append(emb)

# print(f"✅ Generated {len(generated_embeddings)} age-progressed identities")

# # =====================================================
# # CCTV (WEBCAM)
# # =====================================================
# cap = cv2.VideoCapture(0)
# print("🎥 CCTV started — press Q to quit")

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     face = mtcnn(rgb)

#     if face is not None:
#         face = face.unsqueeze(0).to(DEVICE)
#         emb = face_net(face)
#         emb = F.normalize(emb, dim=1)

#         best_sim = 0
#         for gen_emb in generated_embeddings:
#             sim = F.cosine_similarity(emb, gen_emb).item()
#             best_sim = max(best_sim, sim)

#         percent = similarity_to_percent(best_sim)

#         if best_sim > THRESHOLD:
#             text = f"MATCH FOUND: {percent:.1f}%"
#             color = (0, 0, 255)
#         else:
#             text = f"Similarity: {percent:.1f}%"
#             color = (0, 255, 0)

#         cv2.putText(frame, text, (30, 50),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

#     cv2.imshow("Missing Child Detection (Demo)", frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
