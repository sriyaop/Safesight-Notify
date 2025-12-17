import os
from PIL import Image
from facenet_pytorch import MTCNN
from tqdm import tqdm
import torch

INPUT_DIR = "data/cleaned/images/"
OUTPUT_DIR = "data/cleaned/faces/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
mtcnn = MTCNN(keep_all=False, device=device)

failed = []

files = sorted(os.listdir(INPUT_DIR))
for fname in tqdm(files, desc="Cropping faces"):
    img_path = os.path.join(INPUT_DIR, fname)
    try:
        img = Image.open(img_path).convert("RGB")
        face_tensor, prob = mtcnn(img, return_prob=True)  # returns tensor and probability
        if face_tensor is None or prob < 0.90:  # skip low-confidence detections
            failed.append(fname)
            continue

        # Convert tensor to PIL image correctly
        face_img = Image.fromarray((face_tensor.permute(1, 2, 0).int().numpy()).astype('uint8'))

        # Resize to 160x160
        face_img = face_img.resize((160, 160))
        face_img.save(os.path.join(OUTPUT_DIR, fname))

    except Exception as e:
        failed.append(fname)

print(f"\n✅ Face cropping completed. Faces saved in: {OUTPUT_DIR}")
print(f"Failed to detect faces in {len(failed)} images")
if failed:
    print("Examples:", failed[:10])
