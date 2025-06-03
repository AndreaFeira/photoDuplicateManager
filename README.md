
---

## ReadMe

```
Photo Duplicate Manager
=======================

Scans a specified folder (and its subfolders) for exact duplicate images (100% perceptual hash match).
Hashes are computed in parallel, with a real-time progress bar and ETA. Exact duplicates can be moved
to a “duplicates” subfolder under a user-specified path if the -m option is used.

Supported Image Formats:
  .jpg, .jpeg, .png, .bmp, .gif, .tiff, .webp

Usage:
  python3 photo_duplicate_manager.py /path/to/folder
      - Scans the folder recursively and prints groups of exact (100%) duplicate images.
  
  python3 photo_duplicate_manager.py /path/to/folder -m /path/to/destination
      - Same as above, but also moves each lower-byte-size duplicate into:
          /path/to/destination/duplicates/
      - The “original” (largest file) stays in place; all smaller duplicates are relocated.

How It Works:
  1. The script walks through /path/to/folder, gathering all files with supported extensions.
  2. A ProcessPoolExecutor computes a perceptual hash (phash) for each image in parallel.
     While hashing, a progress bar shows “processed/total (percent%) – ETA: xx.xs”.
  3. Images sharing the same phash string are considered exact duplicates.
     They are grouped together in lists of identical files.
  4. If the -m flag is provided, for each group the script identifies the “original” as the
     file with the largest byte size, then moves all other files in that group to:
       /path/to/destination/duplicates/
     Duplicate filenames are adjusted (e.g., “image.jpg” → “image_1.jpg”) if needed
     to avoid overwriting.
  5. Finally, the script prints each group of exact duplicates by listing filenames on a single line.
     At the end, it displays the total runtime in seconds.

Examples:
  $ python3 photo_duplicate_manager.py /home/user/Pictures
  🔍 Computing hashes for 12000 images in parallel...

  [####################-------------] 6000/12000 (50.0%) – ETA: 30.2s

  Comparison results in '/home/user/Pictures':

   • IMG_0001.jpg  |  IMG_0001_copy.jpg
   • vacation01.png  |  vacation01_backup.png  |  vacation01_old.png

  ✅ Completed in 62.75 seconds.

  $ python3 photo_duplicate_manager.py /home/user/Pictures -m /home/user/Sorted
  🔍 Computing hashes for 12000 images in parallel...

  [####################-------------] 6000/12000 (50.0%) – ETA: 30.2s

  Comparison results in '/home/user/Pictures':

   • IMG_0001.jpg  |  IMG_0001_copy.jpg
   • vacation01.png  |  vacation01_backup.png  |  vacation01_old.png

  ✅ Lower-byte-size duplicates have been moved to: /home/user/Sorted/duplicates
  ✅ Completed in 62.75 seconds.

Notes:
  - Corrupted or unreadable images are skipped (returned as None hash).
  - Only exact (100%) phash matches are flagged. For near-duplicate detection (e.g., ≥95%), 
    modify the grouping logic to compare hash distances rather than exact string match.
  - The “original” in each duplicate set is chosen as the largest file by byte size.
  - If a moved duplicate’s filename already exists in the destination folder, the script appends
    _1, _2, etc., to avoid overwriting.
```
