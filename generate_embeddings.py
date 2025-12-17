import os
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN

INPUT_DIR = "data/cleaned/images/"
META_CSV = "data/cleaned/metadata.csv"
OUTPUT_DIR = "data/embeddings/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load models
device = 'cuda' if torch.cuda.is_available() else 'cpu'

mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

print("Models loaded. Processing images...\n")

df = pd.read_csv(META_CSV)
embedding_paths = []

for idx, row in tqdm(df.iterrows(), total=len(df)):
    img_path = os.path.join(INPUT_DIR, row["image_file"])
    try:
        img = Image.open(img_path).convert("RGB")
    except:
        embedding_paths.append("")
        continue

    # Detect face
    face = mtcnn(img)
    if face is None:
        embedding_paths.append("")
        continue

    face = face.unsqueeze(0).to(device)  # add batch dimension

    with torch.no_grad():
        emb = resnet(face).cpu().numpy().flatten()

    # Save embedding
    emb_path = os.path.join(OUTPUT_DIR, row["child_id"] + ".npy")
    np.save(emb_path, emb)

    embedding_paths.append(emb_path)

df["embedding_path"] = embedding_paths
df.to_csv(META_CSV, index=False)

print("\n✅ Embedding generation completed successfully!")
print(f"Embeddings saved in: {OUTPUT_DIR}")
