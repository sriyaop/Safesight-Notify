import os
from PIL import Image
import cv2
from tqdm import tqdm
import imagehash
import hashlib

RAW_DIR = "data/raw/images/"
CLEAN_DIR = "data/cleaned/images/"

def ensure_clean_dir():
    os.makedirs(CLEAN_DIR, exist_ok=True)

def is_corrupted(path):
    try:
        img = Image.open(path)
        img.verify()
        return False
    except:
        return True

def fix_image_format(path):
    try:
        img = Image.open(path).convert("RGB")
        return img
    except:
        return None

def compute_hash(path):
    try:
        img = Image.open(path)
        return str(imagehash.average_hash(img))
    except:
        return None

def main():
    ensure_clean_dir()

    files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    seen_hashes = set()
    counter = 1

    print("\n🔍 Cleaning + Renaming Started...\n")

    for filename in tqdm(files):
        old_path = os.path.join(RAW_DIR, filename)

        # Skip corrupted
        if is_corrupted(old_path):
            print(f"Skipping corrupted file: {filename}")
            continue

        # Fix image format
        img = fix_image_format(old_path)
        if img is None:
            print(f"Error reading file: {filename}")
            continue

        # Detect duplicates (image hashing)
        img_hash = compute_hash(old_path)
        if img_hash in seen_hashes:
            print(f"Duplicate removed: {filename}")
            continue
        seen_hashes.add(img_hash)

        # Rename -> child_0001.jpg
        new_name = f"child_{counter:04}.jpg"
        new_path = os.path.join(CLEAN_DIR, new_name)

        # Save cleaned image
        img.save(new_path, "JPEG", quality=95)

        counter += 1

    print("\n✅ Cleaning Completed!")
    print(f"Total cleaned images: {counter - 1}")
    print("Cleaned files saved to: data/cleaned/images/")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
