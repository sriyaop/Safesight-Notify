import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 128
NUM_BUCKETS = 6
TEAM_CHILD_FOLDER = "data/team_children"
CHECKPOINT = "epoch_30.pt"


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


def build_age_database(metadata_df):

    print("\nBuilding Age Progression Database...")

    G = Generator().to(DEVICE)
    checkpoint = torch.load(CHECKPOINT, map_location=DEVICE)
    G.load_state_dict(checkpoint["G"])
    G.eval()

    mtcnn = MTCNN(image_size=IMG_SIZE, device=DEVICE)
    face_net = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)

    age_db = {}

    for file in os.listdir(TEAM_CHILD_FOLDER):

        name = os.path.splitext(file)[0]

        record = metadata_df[
            metadata_df["child_name"].str.lower() == name.lower()
        ]

        if record.empty:
            print(f"Skipping {file} (no metadata match)")
            continue

        path = os.path.join(TEAM_CHILD_FOLDER, file)
        img = Image.open(path).convert("RGB")

        aligned = mtcnn(img)

        if aligned is None:
            print(f"No face detected in {file}")
            continue

        if aligned.ndim == 3:
            tensor = aligned.unsqueeze(0)
        else:
            tensor = aligned[0].unsqueeze(0)

        tensor = tensor.to(DEVICE)

        refs = []

        with torch.no_grad():

            emb = face_net(tensor)
            emb = F.normalize(emb, dim=1)
            refs.append(emb.cpu().numpy().flatten())

            for bucket in range(NUM_BUCKETS):

                age_tensor = torch.tensor([bucket]).to(DEVICE)
                gen = G(tensor, age_tensor)

                emb = face_net(gen)
                emb = F.normalize(emb, dim=1)

                refs.append(emb.cpu().numpy().flatten())

        age_db[name.lower()] = refs

        print(f"Age embeddings generated for {name}")

    print("Age progression database ready.\n")

    return age_db