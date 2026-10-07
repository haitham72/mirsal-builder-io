"""Batch import manually generated sheets from inputs/ into the gallery.

This script processes all img-NNN-* and vid-NNN-* folders from inputs/Images_gen and inputs/videos_gen
through the pipeline so they appear as batches in the Studio/Library, ready for viewing and export to Telegram.
"""
import sys
from pathlib import Path

# Add mirsal to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "mirsal"))

from mirsal.flow import pipeline as pl, sources, gates
from mirsal.runtime import paths

def main():
    inp = paths.input_root()
    out = paths.out_root()

    print(f"Input root: {inp}")
    print(f"Output root: {out}")
    print()

    # Find all image folders
    img_base = inp / "Images_gen"
    vid_base = inp / "videos_gen"

    if not img_base.exists():
        print(f"No Images_gen folder found at {img_base}")
        return

    # List all folders
    img_folders = sorted([d for d in img_base.iterdir() if d.is_dir() and d.name.startswith("img-")])
    vid_folders = sorted([d for d in vid_base.iterdir() if d.is_dir() and d.name.startswith("vid-")]) if vid_base.exists() else []

    print(f"Found {len(img_folders)} image folders")
    print(f"Found {len(vid_folders)} video folders")
    print()

    # Process each pair
    for img_folder in img_folders:
        # Parse folder name: img-NNN-subject
        parts = img_folder.name.split("-", 2)
        if len(parts) < 3:
            print(f"Skipping {img_folder.name}: invalid format")
            continue

        num, subject = parts[1], parts[2]
        vid_folder = vid_base / f"vid-{num}-{subject}" if vid_base.exists() else None

        print(f"Processing: {img_folder.name} (with video: {vid_folder.name if vid_folder and vid_folder.exists() else 'no'})")

        # Find the sheet file
        sheet_files = list(img_folder.glob("*.png")) + list(img_folder.glob("*.jpg")) + list(img_folder.glob("*.jpeg"))
        if not sheet_files:
            print(f"  No sheet image found, skipping")
            continue

        sheet_file = sheet_files[0]
        print(f"  Sheet: {sheet_file.name}")

        # Find video file if exists
        video_file = None
        if vid_folder and vid_folder.exists():
            video_files = list(vid_folder.glob("*.mp4")) + list(vid_folder.glob("*.mov")) + list(vid_folder.glob("*.webm"))
            if video_files:
                video_file = video_files[0]
                print(f"  Video: {video_file.name}")

        # Create a Pick object
        pick = sources.Pick(
            subject=subject,
            subject_id=num,
            variant=1,
            n_variants=1,
            sheet=sheet_file,
            video=video_file
        )

        # Start the pipeline
        try:
            gid = pl.start(subject.replace("_", " "), out, inp, pick=pick)
            print(f"  → Created batch G{gid:03d}")

            # Run stills
            pl.run_stills(out, gid, pl.Config.default(), pl.Pace.default())
            print(f"  → Stills processed")

            # If video exists, process it
            if video_file:
                # This would need the full video pipeline - for now just note it
                print(f"  → Video found (needs manual processing through Studio)")
            else:
                print(f"  → No video")

            print(f"  ✓ Batch G{gid:03d} ready for viewing in Studio")
            print()

        except Exception as e:
            print(f"  ✗ Error: {e}")
            print()
            continue

    print("Done! You can now view and export these batches in the Studio.")

if __name__ == "__main__":
    main()
