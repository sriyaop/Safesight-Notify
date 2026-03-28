import os

EXCLUDE_FOLDERS = [
    "data/cleaned",
    "data/raw",
    "data/embeddings"
]

EXCLUDE_FILES = [
    "cleaned.zip",
    "data.zip"
]

def print_tree(start_path, prefix=""):
    for item in os.listdir(start_path):
        path = os.path.join(start_path, item)
        normalized_path = path.replace("\\", "/")  # for Windows
        
        print(prefix + "├── " + item)

        # Skip excluded files
        if item in EXCLUDE_FILES:
            continue

        # Skip excluded folders (using full path match)
        if any(normalized_path.endswith(excluded) for excluded in EXCLUDE_FOLDERS):
            print(prefix + "│   └── ... (omitted)")
            continue

        # Recurse into folders
        if os.path.isdir(path):
            print_tree(path, prefix + "│   ")

print_tree(".")