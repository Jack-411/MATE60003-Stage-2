from imports import *

def clear_pycache(folder: Path = None):
    folder = Path(folder or Path(__file__).parent)
    if not folder.exists():
        print(f"Folder {folder} does not exist.")
        return

    deleted = 0
    for pycache in folder.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            print(f"Deleted {pycache}")
            deleted += 1
        except Exception as e:
            print(f"Failed to delete {pycache}: {e}")

    print(f"Cleared {deleted} __pycache__ folders under {folder}")

if __name__ == "__main__":
    pass