"""Découpe un extrait de la vidéo source et lui applique crop + sous-titres."""
import os
import subprocess
from . import crop as crop_mod
from . import subtitles as sub_mod


def cut_segment(source_path: str, start: float, end: float, output_path: str) -> None:
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", source_path, "-t", str(duration),
        "-c:v", "libx264", "-c:a", "aac", "-avoid_negative_ts", "make_zero",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def build_clip(
    source_path: str,
    highlight: dict,
    words: list[dict],
    tracking_mode: str,
    work_dir: str,
    final_output_dir: str,
    index: int,
) -> str:
    """Pipeline complet pour UN extrait: cut -> crop -> sous-titres -> fichier final."""
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(final_output_dir, exist_ok=True)

    start, end = highlight["start"], highlight["end"]
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in highlight.get("title", f"clip{index}"))
    safe_title = safe_title.strip().replace(" ", "_")[:40] or f"clip{index}"

    raw_cut = os.path.join(work_dir, f"{index:02d}_{safe_title}_raw.mp4")
    cropped = os.path.join(work_dir, f"{index:02d}_{safe_title}_cropped.mp4")
    ass_path = os.path.join(work_dir, f"{index:02d}_{safe_title}.ass")
    final_path = os.path.join(final_output_dir, f"{index:02d}_{safe_title}.mp4")

    cut_segment(source_path, start, end, raw_cut)

    if tracking_mode == "advanced":
        crop_mod.crop_advanced(raw_cut, cropped)
    else:
        crop_mod.crop_simple(raw_cut, cropped)

    sub_mod.generate_ass(words, start, end, ass_path)
    sub_mod.burn_subtitles(cropped, ass_path, final_path)

    return final_path
