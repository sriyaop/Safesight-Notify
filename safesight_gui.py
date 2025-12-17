import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine

# ---------------- CONFIG ----------------
META_CSV = "data/cleaned/metadata.csv"
MATCH_THRESHOLD = 0.75
# ---------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load models
mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

# Load database
df = pd.read_csv(META_CSV)
db_embeddings = []
db_records = []

for _, row in df.iterrows():
    if isinstance(row["embedding_path"], str) and row["embedding_path"] != "":
        db_embeddings.append(np.load(row["embedding_path"]))
        db_records.append(row)

# ---------------- FUNCTIONS ----------------

def match_image(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
    except:
        return "Error", "Could not open image"

    face = mtcnn(img)
    if face is None:
        return "No Face", "No face detected"

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
        return best_match["child_name"], f"{match_percent:.2f}%"
    else:
        return "No Match", f"{match_percent:.2f}%"

def upload_image():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )
    if not file_path:
        return

    img = Image.open(file_path)
    img = img.resize((250, 250))
    img_tk = ImageTk.PhotoImage(img)
    image_label.configure(image=img_tk)
    image_label.image = img_tk

    name, score = match_image(file_path)
    result_label.config(text=f"Name: {name}")
    score_label.config(text=f"Match: {score}")

# ---------------- GUI ----------------

root = tk.Tk()
root.title("SafeSightNotify - Missing Child Identification")
root.geometry("500x600")

title = tk.Label(root, text="SafeSightNotify", font=("Arial", 20, "bold"))
title.pack(pady=10)

image_label = tk.Label(root)
image_label.pack(pady=10)

upload_btn = tk.Button(root, text="Upload Image", command=upload_image, width=20)
upload_btn.pack(pady=10)

result_label = tk.Label(root, text="Name: ", font=("Arial", 14))
result_label.pack(pady=5)

score_label = tk.Label(root, text="Match: ", font=("Arial", 14))
score_label.pack(pady=5)

footer = tk.Label(root, text="AI-Based Face Recognition System", fg="gray")
footer.pack(side="bottom", pady=10)

root.mainloop()
