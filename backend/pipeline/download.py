"""Télécharge une vidéo depuis une URL (YouTube, etc.) via yt-dlp."""
import os
import yt_dlp


def download_video(url: str, output_dir: str = "downloads") -> tuple[str, dict]:
    """Télécharge la vidéo et retourne (chemin_fichier_mp4, infos_metadata)."""
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filepath)
        mp4_path = base + ".mp4"
        if os.path.exists(mp4_path):
            filepath = mp4_path

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Échec du téléchargement: {url}")

    return filepath, info
