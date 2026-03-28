from dotenv import load_dotenv
load_dotenv()

from flask_cors import CORS
import os
import threading
import base64
import numpy as np
import cv2
import torch
import pandas as pd
from flask import Flask, jsonify, Response

from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine

from age_module import build_age_database
from sort_tracker import SortTracker

from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

import logging

# ----------------------------------
# INIT
# ----------------------------------

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

print("\n========================================")
print(" SafeSightNotify Web Server Started")
print("========================================\n")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ----------------------------------
# CONFIG
# ----------------------------------

CAMERAS = {
    "PeopleLink": 0,
    "Laptop": 1,
    "Zebronics": 2
}

MATCH_THRESHOLD = 0.78  # 🔥 stricter

META_CSV = "data/cleaned/metadata_private.csv"

EMAIL_SENDER = "sriyabommakanti@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

device = "cuda" if torch.cuda.is_available() else "cpu"

# ----------------------------------
# MODELS
# ----------------------------------

mtcnn = MTCNN(image_size=160, margin=10, keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

# ----------------------------------
# DATABASE
# ----------------------------------

df = pd.read_csv(META_CSV)

print("\nBuilding Age Database...")
age_database = build_age_database(df)
print("Age DB Ready\n")

db_embeddings = []
db_records = []

for _, row in df.iterrows():
    if isinstance(row.get("embedding_path"), str):
        emb = np.load(row["embedding_path"])
        db_embeddings.append(emb)
        db_records.append(row)

print("Total DB embeddings:", len(db_embeddings))

# ----------------------------------
# GLOBAL STATE
# ----------------------------------

camera_frames = {}
camera_results = {}
alerted_faces = {}
COOLDOWN = 20  # seconds

for cam in CAMERAS:
    camera_frames[cam] = np.zeros((480, 640, 3), dtype=np.uint8)
    camera_results[cam] = []

tracker = SortTracker()

# ----------------------------------
# EMAIL
# ----------------------------------

def send_email_alert(name, confidence, face_img):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_SENDER
        msg["Subject"] = f"🚨 Match Found: {name}"

        body = f"""
        Match detected!

        Name: {name}
        Confidence: {confidence}%
        Time: {datetime.now()}
        """

        msg.attach(MIMEText(body, "plain"))

        img_data = base64.b64decode(face_img.split(",")[1])
        image = MIMEImage(img_data)
        msg.attach(image)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("📧 Email sent:", name)

    except Exception as e:
        print("❌ Email error:", e)

# ----------------------------------
# MATCHING
# ----------------------------------

def match_embedding(query_emb):
    best_score = 0
    best_record = None

    # NORMAL
    for db_emb, record in zip(db_embeddings, db_records):
        score = 1 - cosine(query_emb, db_emb)

        if score > best_score:
            best_score = score
            best_record = record

    # AGE
    for name, age_emb_list in age_database.items():
        for age_emb in age_emb_list:
            score = (1 - cosine(query_emb, age_emb)) * 1.1

            if score > best_score:
                best_score = score
                best_record = next(
                    (r for r in db_records if r["child_name"] == name),
                    {"child_name": name}
                )

    return best_score, best_record

# ----------------------------------
# CAMERA
# ----------------------------------

def process_camera(camera_name, index):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Camera failed:", camera_name)
        return

    print("✅ Camera opened:", camera_name)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        boxes, _ = mtcnn.detect(rgb)
        faces = mtcnn(rgb)

        results = []

        if faces is not None and boxes is not None:
            for i, face in enumerate(faces):

                with torch.no_grad():
                    emb = resnet(face.unsqueeze(0).to(device)).cpu().numpy().flatten()

                score, record = match_embedding(emb)

                if record is None or score < MATCH_THRESHOLD:
                    continue

                name = record.get("child_name", "Unknown")

                now = datetime.now().timestamp()

                # 🔥 cooldown instead of spam
                if name in alerted_faces:
                    if now - alerted_faces[name] < COOLDOWN:
                        continue

                alerted_faces[name] = now

                x1, y1, x2, y2 = map(int, boxes[i])

                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                _, buffer = cv2.imencode(".jpg", face_crop)

                face_base64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode()

                print(f"✅ MATCH: {name} ({score:.2f})")

                send_email_alert(name, round(score * 100, 2), face_base64)

                results.append({
                    "name": name,
                    "confidence": round(score * 100, 2),
                    "face": face_base64,
                    "db_image": ""
                })

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        camera_frames[camera_name] = frame
        camera_results[camera_name] = results

# ----------------------------------
# START
# ----------------------------------

def start_cameras():
    for cam, idx in CAMERAS.items():
        threading.Thread(target=process_camera, args=(cam, idx), daemon=True).start()

# ----------------------------------
# ROUTES
# ----------------------------------

@app.route("/")
def home():
    return {"status": "running"}

@app.route("/metrics")
def metrics():
    return jsonify({
        "missing_children": len(db_records),
        "detections_today": sum(len(v) for v in camera_results.values()),
        "active_alerts": len(alerted_faces)
    })

@app.route("/camera_results")
def results():
    return jsonify(camera_results)

@app.route("/children")
def children():
    return jsonify([
        {
            "name": row.get("child_name"),
            "age": row.get("age"),
            "gender": row.get("gender"),
            "last_seen": row.get("last_seen")
        }
        for _, row in df.iterrows()
    ])

@app.route("/video_feed/<camera>")
def video_feed(camera):

    mapping = {
        "peoplelink": "PeopleLink",
        "laptop": "Laptop",
        "zebronics": "Zebronics"
    }

    camera = mapping.get(camera.lower(), camera)

    def generate():
        while True:
            frame = camera_frames.get(camera)

            if frame is None:
                continue

            _, buffer = cv2.imencode(".jpg", frame)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ----------------------------------
# MAIN
# ----------------------------------

if __name__ == "__main__":
    threading.Thread(target=start_cameras, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True, use_reloader=False)