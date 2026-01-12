import os
import numpy as np
from PIL import Image
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1

CUSTOM_IMG_DIR = "data/custom/images/"
OUTPUT_EMB_DIR = "data/custom/embeddings/"
META_CSV = "data/cleaned/metadata.csv"

os.makedirs(OUTPUT_EMB_DIR, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"

mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

df = pd.read_csv(META_CSV)

# Continue IDs from last synthetic child
start_index = len(df) + 1

new_rows = []

for idx, filename in enumerate(os.listdir(CUSTOM_IMG_DIR), start=start_index):
    img_path = os.path.join(CUSTOM_IMG_DIR, filename)

    # Generate face embedding
    try:
        img = Image.open(img_path).convert("RGB")
    except:
        print(f"Cannot open {filename}")
        continue

    face = mtcnn(img)

    if face is None:
        print(f"No face detected in {filename}")
        continue

    face = face.unsqueeze(0).to(device)

    with torch.no_grad():
        emb = resnet(face).cpu().numpy().flatten()

    emb_path = os.path.join(OUTPUT_EMB_DIR, f"C_{idx:05d}.npy")
    np.save(emb_path, emb)

    # CREATE A SYNTHETIC PROFILE FOR YOU OR TEAMMATE
    new_rows.append({
        "child_id": f"C_{idx:05d}",
        "image_file": filename,

        # YOU WILL EDIT THESE NAMES LATER IF NEEDED
        "child_name": filename.split(".")[0].capitalize(),
        "father_name": "Test Father",
        "mother_name": "Test Mother",

        "age": 20,
        "gender": "F",
        "missing_city": "Hyderabad",
        "last_seen_area": "Gachibowli",
        "days_missing": 0,
        "phone_number": "+91-90000-00001",

        # 🔥 THIS IS THE KEY PART
        "parent_email": "teammate_email@gmail.com",   # CHANGE PER PERSON
        "police_email": "YOUR_EMAIL@gmail.com",        # YOUR email (demo police)

        "profile_type": "TEST",
        "embedding_path": emb_path
})


df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
df.to_csv(META_CSV, index=False)

print("Custom users added successfully!")
