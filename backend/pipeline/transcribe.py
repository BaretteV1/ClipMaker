"""Transcrit une vidéo via Gemini (audio) — un seul provider (Gemini) pour tout le pipeline."""
import os
import json
import subprocess
from google import genai


def _extract_audio(video_path: str) -> str:
    audio_path = video_path + ".audio.mp3"
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", audio_path]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_path


def _split_words(segment: dict) -> list[dict]:
    """Gemini ne donne pas de timing mot-par-mot fiable -> on l'estime en répartissant
    la durée du segment proportionnellement à la longueur de chaque mot."""
    text = segment["text"].strip()
    words_raw = text.split()
    if not words_raw:
        return []
    dur = max(segment["end"] - segment["start"], 0.01)
    total_chars = sum(len(w) for w in words_raw) or 1
    words, t = [], segment["start"]
    for w in words_raw:
        share = (len(w) / total_chars) * dur
        words.append({"start": t, "end": t + share, "word": w})
        t += share
    return words


def transcribe(video_path: str, language: str | None = None) -> dict:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    audio_path = _extract_audio(video_path)
    uploaded = client.files.upload(file=audio_path)

    prompt = (
        "Transcris cet audio en entier, du début à la fin, dans sa langue d'origine. "
        "Découpe en segments courts (5 à 12 mots chacun). Réponds STRICTEMENT en JSON, "
        "sans aucun texte autour, format: "
        '[{"start": 0.0, "end": 2.3, "text": "..."}, ...] '
        "avec start/end en secondes, aussi précis que possible."
    )
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded, prompt],
    )
    content = resp.text.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    segments = json.loads(content)
    words = []
    for s in segments:
        words.extend(_split_words(s))

    os.remove(audio_path)
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass

    return {"segments": segments, "words": words, "language": language or "auto"}
