import os
import math

# 🔧 CONFIG
ROOT_DIR = "."
INCLUDE_EXTENSIONS = [".py", ".html", ".js", ".css", ".json"]
EXCLUDE_FOLDERS = ["data", "venv", "node_modules", ".git", "__pycache__"]

OUTPUT_PREFIX = "project_dump_part_"
NUM_PARTS = 5


def should_skip(path):
    normalized = path.replace("\\", "/")
    return any(f"/{folder}" in normalized for folder in EXCLUDE_FOLDERS)


def collect_all_code():
    all_content = []

    for root, dirs, files in os.walk(ROOT_DIR):

        if should_skip(root):
            continue

        folder_block = []
        folder_block.append("\n" + "="*80)
        folder_block.append(f"📁 FOLDER: {root}")
        folder_block.append("="*80 + "\n")

        for file in files:
            if any(file.endswith(ext) for ext in INCLUDE_EXTENSIONS):

                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    content = f"[ERROR READING FILE]: {e}"

                file_block = [
                    "\n" + "-"*60,
                    f"📄 FILE: {file}",
                    f"📍 PATH: {file_path}",
                    "-"*60 + "\n",
                    content,
                    "\n"
                ]

                folder_block.extend(file_block)

        all_content.append("\n".join(folder_block))

    return "\n".join(all_content)


def split_into_parts(full_text):
    length = len(full_text)
    part_size = math.ceil(length / NUM_PARTS)

    for i in range(NUM_PARTS):
        start = i * part_size
        end = start + part_size

        part_content = full_text[start:end]

        filename = f"{OUTPUT_PREFIX}{i+1}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(part_content)

        print(f"✅ Created {filename}")


def main():
    print("📦 Collecting project code...")
    full_text = collect_all_code()

    print("✂️ Splitting into parts...")
    split_into_parts(full_text)

    print("🎉 Done! 5 files ready.")


main()