import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import pandas as pd
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine
from datetime import datetime
import os

ALERT_COOLDOWN_SECONDS = 10
last_alert_time = None

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "YOUR_APP_PASSWORD"   # Gmail App Password
EMAIL_RECEIVER = "receiver_email@gmail.com"

def send_email_alert(record, match_pct, source):
    subject = "🚨 SafeSightNotify Alert — Match Found"
    body = f"""
MATCH FOUND!

Name: {record['child_name']}
Age: {record['age']}
Gender: {record['gender']}
City: {record['missing_city']}
Last Seen Area: {record['last_seen_area']}

Match Confidence: {match_pct:.2f}%
Source: {source}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

— SafeSightNotify
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email failed:", e)

from tkinter import messagebox

def popup_alert(record, match_pct, source):
    messagebox.showwarning(
        "🚨 MATCH FOUND",
        f"Name: {record['child_name']}\n"
        f"Match: {match_pct:.2f}%\n"
        f"City: {record['missing_city']}\n"
        f"Source: {source}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# ---------------- CONFIG ----------------
META_CSV = "data/cleaned/metadata.csv"
LOG_FILE = "data/logs/last_seen.csv"
MATCH_THRESHOLD = 0.75
CAMERA_INDEX = 0
# ---------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"

# Models
mtcnn = MTCNN(keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

# Load DB
df = pd.read_csv(META_CSV)
db_embeddings = []
db_records = []

for _, row in df.iterrows():
    if isinstance(row["embedding_path"], str) and row["embedding_path"]:
        db_embeddings.append(np.load(row["embedding_path"]))
        db_records.append(row)

# ---------------- FUNCTIONS ----------------

def log_last_seen(record, match_pct, source):
    os.makedirs("data/logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_row = {
        "child_id": record["child_id"],
        "child_name": record["child_name"],
        "match_percentage": round(match_pct, 2),
        "timestamp": timestamp,
        "source": source
    }
    df_log = pd.DataFrame([log_row])
    df_log.to_csv(LOG_FILE, mode="a", header=not os.path.exists(LOG_FILE), index=False)

def match_embedding(query_emb, source="IMAGE"):
    results = []

    for db_emb, record in zip(db_embeddings, db_records):
        score = 1 - cosine(query_emb, db_emb)
        if score >= MATCH_THRESHOLD:
            results.append((score, record))

    results.sort(key=lambda x: x[0], reverse=True)
    return results

def format_metadata(record, score):
    return (
        f"Name: {record['child_name']}\n"
        f"Age: {record['age']}\n"
        f"Gender: {record['gender']}\n"
        f"City: {record['missing_city']}\n"
        f"Last Seen: {record['last_seen_area']}\n"
        f"Parents: {record['father_name']} / {record['mother_name']}\n"
        f"Phone: {record['phone_number']}\n"
        f"Match: {score*100:.2f}%\n"
        "--------------------------\n"
    )

def upload_image():
    path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )
    if not path:
        return

    img = Image.open(path).resize((250, 250))
    img_tk = ImageTk.PhotoImage(img)
    image_label.configure(image=img_tk)
    image_label.image = img_tk

    face = mtcnn(Image.open(path).convert("RGB"))
    if face is None:
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, "No face detected.")
        return

    with torch.no_grad():
        emb = resnet(face.unsqueeze(0).to(device)).cpu().numpy().flatten()

    matches = match_embedding(emb, source="IMAGE")
    output_box.delete("1.0", tk.END)

    if not matches:
        output_box.insert(tk.END, "No match found.")
        return

    global last_alert_time

    top_score, top_record = matches[0]

    # Show metadata (all matches)
    for score, record in matches:
        log_last_seen(record, score * 100, "IMAGE")
        output_box.insert(tk.END, format_metadata(record, score))

    # Trigger alert only once
    now = datetime.now()
    if last_alert_time is None or (now - last_alert_time).seconds > ALERT_COOLDOWN_SECONDS:
        popup_alert(top_record, top_score * 100, "IMAGE")
        send_email_alert(top_record, top_score * 100, "IMAGE")
        last_alert_time = now

# ---------------- LIVE CAMERA ----------------

def start_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    def update_frame():
        ret, frame = cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face = mtcnn(rgb)

        label = "NO MATCH"

        if face is not None:
            with torch.no_grad():
                emb = resnet(face.unsqueeze(0).to(device)).cpu().numpy().flatten()

            matches = match_embedding(emb, source="CAMERA")
            output_box.delete("1.0", tk.END)

        global last_alert_time

        if matches:
            top_score, top_record = matches[0]

            output_box.delete("1.0", tk.END)

            # Show top 3 matches (descending)
            for score, record in matches[:3]:
                log_last_seen(record, score * 100, "CAMERA")
                output_box.insert(tk.END, format_metadata(record, score))

            label = f"MATCH ({top_score*100:.1f}%)"

            # ALERT (with cooldown)
            now = datetime.now()
            if last_alert_time is None or (now - last_alert_time).seconds > ALERT_COOLDOWN_SECONDS:
                popup_alert(top_record, top_score * 100, "CAMERA")
                send_email_alert(top_record, top_score * 100, "CAMERA")
                last_alert_time = now

        cv2.putText(frame, label, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)

        img = ImageTk.PhotoImage(Image.fromarray(rgb).resize((300, 250)))
        cam_label.configure(image=img)
        cam_label.image = img

        root.after(30, update_frame)

    update_frame()

# ---------------- GUI ----------------

root = tk.Tk()
root.title("SafeSightNotify — Live Missing Child Detection")
root.geometry("800x700")

tk.Label(root, text="SafeSightNotify", font=("Arial", 22, "bold")).pack(pady=10)

top_frame = tk.Frame(root)
top_frame.pack()

image_label = tk.Label(top_frame)
image_label.grid(row=0, column=0, padx=10)

cam_label = tk.Label(top_frame)
cam_label.grid(row=0, column=1, padx=10)

tk.Button(root, text="Upload Image", width=20, command=upload_image).pack(pady=5)
tk.Button(root, text="Start Live Camera", width=20, command=start_camera).pack(pady=5)

output_box = tk.Text(root, height=15, width=90)
output_box.pack(pady=10)

root.mainloop()
