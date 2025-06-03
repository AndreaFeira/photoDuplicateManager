import os
import sys
import time
import shutil
from PIL import Image
import imagehash
from concurrent.futures import ProcessPoolExecutor

# Supported image extensions
FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

def find_images(folder_path):
    """
    Recursively walk through the given folder and collect all files
    whose names end with one of the supported image extensions.
    Returns a list of full file paths.
    """
    images = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith(FORMATS):
                images.append(os.path.join(root, filename))
    return images

def print_progress_bar(current, total, width=40, eta=None):
    """
    Display a progress bar on a single terminal line.
    - current: number of items processed so far
    - total: total number of items to process
    - width: total width (characters) of the bar
    - eta: optional estimated time remaining (in seconds)
    """
    fraction = current / total if total > 0 else 1
    done_width = int(fraction * width)
    bar = "#" * done_width + "-" * (width - done_width)
    if eta is not None:
        print(f"\r[{bar}] {current}/{total} ({round(fraction * 100, 2)}%) – ETA: {round(eta, 1)}s", end='', flush=True)
    else:
        print(f"\r[{bar}] {current}/{total} ({round(fraction * 100, 2)}%)", end='', flush=True)

def safe_compute_hash(image_path):
    """
    Attempt to open the image at image_path and compute its perceptual hash (phash).
    Returns a tuple (image_path, hash) or (image_path, None) on error.
    """
    try:
        with Image.open(image_path) as img:
            return image_path, imagehash.phash(img)
    except Exception:
        return image_path, None

def group_exact_duplicates(hash_dict):
    """
    Given a dictionary mapping file paths → phash (or None), group together
    all file paths that share the same hash string. Only groups with ≥2 files
    are returned (i.e., exact duplicates).
    Returns a list of lists; each inner list is a group of file paths.
    """
    mapping = {}
    for filepath, ph in hash_dict.items():
        if ph is None:
            continue
        key = str(ph)
        mapping.setdefault(key, []).append(filepath)
    return [group for group in mapping.values() if len(group) > 1]

def move_duplicate(src_file, duplicates_dir):
    """
    Move the src_file into duplicates_dir. If a file with the same name exists,
    append _1, _2, etc. to avoid overwriting.
    """
    os.makedirs(duplicates_dir, exist_ok=True)
    name = os.path.basename(src_file)
    dest = os.path.join(duplicates_dir, name)
    base, ext = os.path.splitext(name)
    i = 1
    while os.path.exists(dest):
        dest = os.path.join(duplicates_dir, f"{base}_{i}{ext}")
        i += 1
    shutil.move(src_file, dest)

def compare_images(folder_path, move_path=None):
    """
    1) Find all images under folder_path.
    2) Compute perceptual hashes in parallel, displaying a progress bar with ETA.
    3) Group images whose hashes match exactly (100% duplicates).
    4) If move_path is provided (via -m), move the lower-byte-size duplicates into move_path/duplicates/.
    5) Print final results.
    """
    # 1) Find all images
    images = find_images(folder_path)
    n_images = len(images)

    # 2) Compute hashes in parallel with progress bar and ETA
    print(f"\n🔍 Computing hashes for {n_images} images in parallel...\n")
    hash_dict = {}
    start_time = time.time()

    with ProcessPoolExecutor() as executor:
        for i, (img_path, ph) in enumerate(executor.map(safe_compute_hash, images), start=1):
            hash_dict[img_path] = ph
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = avg_time * (n_images - i)
            print_progress_bar(i, n_images, eta=remaining)
    print()  # Move to next line after finishing the bar

    # 3) Group images with identical hashes (100% duplicates)
    exact_groups = group_exact_duplicates(hash_dict)

    # 4) If requested, move the lower-byte-size duplicates
    if move_path:
        duplicates_dir = os.path.join(move_path, "duplicates")
        for group in exact_groups:
            # Choose the original as the largest file
            original = max(group, key=lambda p: os.path.getsize(p))
            for img in group:
                if img != original:
                    move_duplicate(img, duplicates_dir)

    # 5) Print final results
    print(f"\n\nComparison results in '{folder_path}':\n")
    if not exact_groups:
        print("❌ No exact (100%) duplicates found.")
    else:
        for group in exact_groups:
            print(" • " + "  |  ".join(os.path.basename(p) for p in group))
        if move_path:
            print(f"\n✅ Lower-byte-size duplicates have been moved to: {os.path.join(move_path, 'duplicates')}")

    total_time = round(time.time() - start_time, 2)
    print(f"\n✅ Completed in {total_time} seconds.")

if __name__ == "__main__":
    if len(sys.argv) not in (2, 4) or (len(sys.argv) == 4 and sys.argv[2] != "-m"):
        print("Usage:\n"
              "  python3 photo_duplicate_manager.py /path/to/folder\n"
              "  python3 photo_duplicate_manager.py /path/to/folder -m /path/to/destination")
        sys.exit(1)

    folder = sys.argv[1]
    move_folder = None
    if len(sys.argv) == 4:
        move_folder = sys.argv[3]

    compare_images(folder, move_folder)
