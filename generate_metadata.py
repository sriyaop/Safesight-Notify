import os
import pandas as pd
import random
from faker import Faker

INPUT_DIR = "data/cleaned/images/"
OUTPUT_CSV = "data/cleaned/metadata.csv"

fake = Faker("en_IN")  # Indian names

files = sorted(os.listdir(INPUT_DIR))

rows = []

for index, filename in enumerate(files, start=1):

    child_id = f"C_{index:05d}"

    # Synthetic names
    child_name = fake.first_name() + " " + fake.last_name()
    father_name = fake.first_name() + " " + fake.last_name()
    mother_name = fake.first_name_female() + " " + fake.last_name()

    # Child attributes
    age = random.randint(3, 15)
    gender = random.choice(["M", "F"])

    # Locations
    city = fake.city()
    last_seen_area = fake.street_name() + ", " + city

    # Phone (neutral pattern)
    phone_number = f"+91-90000-{index:05d}"

    # Default dynamic fields
    days_missing = 0

    rows.append({
        "child_id": child_id,
        "image_file": filename,
        "child_name": child_name,
        "father_name": father_name,
        "mother_name": mother_name,
        "age": age,
        "gender": gender,
        "missing_city": city,
        "last_seen_area": last_seen_area,
        "days_missing": days_missing,
        "phone_number": phone_number,
        "profile_type": "SYNTHETIC"
    })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Metadata generated for {len(df)} images.")
print(f"Saved to: {OUTPUT_CSV}")
