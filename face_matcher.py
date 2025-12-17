import os
import numpy as np
import pandas as pd
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from tqdm import tqdm
from scipy.spatial.distance import cosine

# Setup
device = "cuda" if torch.cuda.is_available() else "cpu"
mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

META_CSV = "data/cleaned/metadata.csv"
df = pd.read_csv(META_CSV)

def get_embedding_from_image(img_path):
    try:
        img = Image.open(img_path).convert("RGB")
    except:
        print("Error: Could not open image.")
        return None

    face = mtcnn(img)

    if face is None:
        print("No face detected in query image.")
        return None

    face = face.unsqueeze(0).to(device)

    with torch.no_grad():
        emb = resnet(face).cpu().numpy().flatten()

    return emb


def match_face(query_image_path, top_k=5):
    query_emb = get_embedding_from_image(query_image_path)

    if query_emb is None:
        return None

    results = []

    for i, row in df.iterrows():
        emb_path = row["embedding_path"]

        if not isinstance(emb_path, str) or emb_path.strip() == "":
            continue

        db_emb = np.load(emb_path)

        # Cosine similarity
        sim = 1 - cosine(query_emb, db_emb)

        results.append({
            "child_id": row["child_id"],
            "child_name": row["child_name"],
            "image_file": row["image_file"],
            "similarity": sim
        })

    # Sort high → low
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)

    # Convert similarity to %
    for r in results:
        r["match_percentage"] = round(float(r["similarity"]) * 100, 2)

    return results[:top_k]


if __name__ == "__main__":
    query = input("Enter path to query image: ")
    matches = match_face(query)

    if matches is None:
        print("No match.")
    else:
        print("\nTop Matches:\n")
        for m in matches:
            print(f"Child ID: {m['child_id']}")
            print(f"Name: {m['child_name']}")
            print(f"Image: {m['image_file']}")
            print(f"Match: {m['match_percentage']}%")
            print("---------------")
