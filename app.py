import os
import threading
import time

from sort_tracker import SortTracker
from age_module import build_age_database
from flask import Flask, render_template, jsonify, Response

import base64
import numpy as np
import cv2
import torch
import pandas as pd

from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine

from datetime import datetime
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

print("\n========================================")
print(" SafeSightNotify Web Server Started")
print(" Open: http://127.0.0.1:5000")
print("========================================\n")

app = Flask(__name__)

# ----------------------------------
# CAMERA CONFIG
# ----------------------------------

CAMERAS = {
    "peoplelink": 0,
    "laptop":1,
    "zebronics":2
}

camera_frames = {}
camera_results = {}

# ----------------------------------

alerted_faces = set()

META_CSV = "data/cleaned/metadata_private.csv"
MATCH_THRESHOLD = 0.65

EMAIL_SENDER = "sriyabommakanti@gmail.com"
EMAIL_PASSWORD = "kyka jddt vqiz nnux"

device = "cuda" if torch.cuda.is_available() else "cpu"

# mtcnn = MTCNN(image_size=128, keep_all=True, device=device)
mtcnn = MTCNN(
    image_size=160,
    margin=10,
    min_face_size=20,
    thresholds=[0.5,0.6,0.6],
    factor=0.6,
    keep_all=True,
    device=device
)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

df = pd.read_csv(META_CSV)

age_database = build_age_database(df)

db_embeddings = []
db_records = []

for _, row in df.iterrows():
    if isinstance(row.get("embedding_path"), str):
        db_embeddings.append(np.load(row["embedding_path"]))
        db_records.append(row)

tracker = SortTracker()

# ----------------------------------
# MATCHING
# ----------------------------------

def match_embedding(query_emb):

    best_score = 0
    best_record = None

    for db_emb, record in zip(db_embeddings, db_records):

        score = 1 - cosine(query_emb, db_emb)

        if score > best_score:
            best_score = score
            best_record = record

    return best_score, best_record


# ----------------------------------
# METRICS
# ----------------------------------

def get_missing_children_count():

    folder = "data/custom/images"

    if not os.path.exists(folder):
        return 0

    names = set()

    for file in os.listdir(folder):

        if file.lower().endswith((".jpg",".jpeg",".png")):

            name = file.split("_")[0].lower()
            names.add(name)

    return len(names)


# ----------------------------------
# EMAIL ALERT
# ----------------------------------

def send_email(record, score, latitude, longitude, face_crop):

    if face_crop is None or face_crop.size == 0:
        return

    child_id = record["child_id"]

    if child_id in alerted_faces:
        return

    alerted_faces.add(child_id)

    receivers = []

    if pd.notna(record.get("parent_email")):
        receivers.append(record["parent_email"])

    if pd.notna(record.get("police_email")):
        receivers.append(record["police_email"])

    if not receivers:
        return

    maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"

    body = f"""
SAFE SIGHT NOTIFY — EMERGENCY ALERT

Child Name: {record['child_name']}
Match Confidence: {score*100:.2f}%

Location:
Latitude: {latitude}
Longitude: {longitude}

Maps:
{maps_link}

Time:
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    try:

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        msg = MIMEMultipart()

        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(receivers)
        msg["Subject"] = "SafeSightNotify Emergency Alert"

        msg.attach(MIMEText(body, "plain"))

        _, buffer = cv2.imencode(".jpg", face_crop)

        img = MIMEImage(buffer.tobytes())
        img.add_header("Content-Disposition", "attachment", filename="detected_face.jpg")

        msg.attach(img)

        server.sendmail(EMAIL_SENDER, receivers, msg.as_string())
        server.quit()

        print("EMAIL ALERT SENT:", record["child_name"])

    except Exception as e:
        print("EMAIL ERROR:", e)


# ----------------------------------
# CAMERA PROCESSOR THREAD
# ----------------------------------

def process_camera(camera_name, index):

    print(f"Opening camera {camera_name} at index {index}")

    # IMPORTANT: PeopleLink cameras require DSHOW backend
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Camera failed:", camera_name)
        return

    print("✅ Camera opened:", camera_name)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)

    # warm up camera
    for i in range(10):
        cap.read()

    camera_frames[camera_name] = np.zeros((480,640,3), dtype=np.uint8)

    while True:

        ret, frame = cap.read()

        if not ret or frame is None:
            print("⚠ Frame grab failed. Retrying...")
            time.sleep(0.2)
            continue

        frame = cv2.resize(frame,(640,480))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (960,720))

        orig_h, orig_w = frame.shape[:2]
        scale_x = orig_w / 960
        scale_y = orig_h / 720

        boxes, _ = mtcnn.detect(rgb)
        faces = mtcnn(rgb)

        results = []

        if faces is not None and boxes is not None:

            for i, face in enumerate(faces):

                with torch.no_grad():
                    emb = resnet(face.unsqueeze(0).to(device)).cpu().numpy().flatten()

                best_score, best_record = match_embedding(emb)

                if best_record is None or best_score < MATCH_THRESHOLD:
                    continue

                x1, y1, x2, y2 = boxes[i]

                x1 = int(x1 * scale_x)
                x2 = int(x2 * scale_x)
                y1 = int(y1 * scale_y)
                y2 = int(y2 * scale_y)

                h, w, _ = frame.shape
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                face_crop = frame[y1:y2, x1:x2]

                if face_crop.size == 0:
                    continue

                send_email(best_record, best_score, 0, 0, face_crop)

                _, buffer = cv2.imencode(".jpg", face_crop)
                face_base64 = base64.b64encode(buffer).decode("utf-8")

                db_image = f"/static/database/{best_record['child_name'].lower()}.jpg"

                results.append({
                    "name": best_record["child_name"],
                    "confidence": round(best_score*100,2),
                    "face": face_base64,
                    "db_image": db_image
                })

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

        camera_frames[camera_name] = frame
        camera_results[camera_name] = results

        time.sleep(0.8)
    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        print("Camera failed:", camera_name)
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)

    # Warm-up camera (important for PeopleLink)
    for i in range(15):
        cap.read()

    camera_frames[camera_name] = np.zeros((480,640,3), dtype=np.uint8)

    while True:

        ret, frame = cap.read()

        if not ret or frame is None:
            time.sleep(0.1)
            continue

        frame = cv2.resize(frame,(640,480))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        boxes, _ = mtcnn.detect(rgb)
        faces = mtcnn(rgb)

        results = []

        if faces is not None and boxes is not None:

            detections = []

            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                detections.append([x1,y1,x2,y2])

            tracker.update(detections)

            for i, face in enumerate(faces):

                with torch.no_grad():
                    emb = resnet(face.unsqueeze(0).to(device)).cpu().numpy().flatten()

                best_score, best_record = match_embedding(emb)

                if best_record is None or best_score < MATCH_THRESHOLD:
                    continue

                x1, y1, x2, y2 = map(int, boxes[i])

                h, w, _ = frame.shape

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                face_crop = frame[y1:y2, x1:x2]

                if face_crop.size == 0:
                    continue

                send_email(best_record, best_score, 0, 0, face_crop)

                _, buffer = cv2.imencode(".jpg", face_crop)
                face_base64 = base64.b64encode(buffer).decode("utf-8")

                db_image = f"/static/database/{best_record['child_name'].lower()}.jpg"

                results.append({
                    "name": best_record["child_name"],
                    "confidence": round(best_score*100,2),
                    "face": face_base64,
                    "db_image": db_image
                })

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

        camera_frames[camera_name] = frame
        camera_results[camera_name] = results

        time.sleep(0.5)


# ----------------------------------
# START CAMERA THREADS
# ----------------------------------

def start_cameras():

    print("Starting camera threads...")

    time.sleep(2)

    for cam_name, idx in CAMERAS.items():

        print("Starting camera:", cam_name)

        t = threading.Thread(
            target=process_camera,
            args=(cam_name, idx),
            daemon=True
        )

        t.start()


# ----------------------------------
# STREAM ROUTE
# ----------------------------------

@app.route("/video_feed/<camera>")
def video_feed(camera):

    def generate():

        while True:

            frame = camera_frames.get(camera)

            if frame is None:
                time.sleep(0.1)
                continue

            _, buffer = cv2.imencode(".jpg", frame)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')

    return Response(generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/camera_results")
def results():
    return jsonify(camera_results)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/metrics")
def metrics():

    return jsonify({
        "missing_children": get_missing_children_count()
    })


if __name__ == "__main__":

    start_cameras()

    app.run(debug=True, threaded=True, use_reloader=False)