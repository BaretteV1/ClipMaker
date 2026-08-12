"""Génère des sous-titres .ass (style karaoké, mot en cours surligné) et les incruste."""
import subprocess

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,2,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _group_words_into_lines(words: list[dict], max_words_per_line: int = 4) -> list[list[dict]]:
    lines = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= max_words_per_line:
            lines.append(current)
            current = []
    if current:
        lines.append(current)
    return lines


def generate_ass(words: list[dict], clip_start: float, clip_end: float, output_path: str) -> str:
    """words: timestamps ABSOLUS (par rapport à la vidéo source). On les recale sur le clip."""
    clip_words = [w for w in words if clip_start <= w["start"] < clip_end]
    # recale à 0
    for w in clip_words:
        w = w.copy()
    lines = _group_words_into_lines(
        [{"word": w["word"], "start": w["start"] - clip_start, "end": w["end"] - clip_start} for w in clip_words]
    )

    events = []
    for line in lines:
        line_start = line[0]["start"]
        line_end = line[-1]["end"]
        full_text = " ".join(w["word"] for w in line)
        # highlight mot par mot: on génère une ligne par mot actif (karaoké simple)
        for i, w in enumerate(line):
            words_render = []
            for j, ww in enumerate(line):
                if j == i:
                    words_render.append(r"{\c&H00FFFF&}" + ww["word"] + r"{\c&HFFFFFF&}")
                else:
                    words_render.append(ww["word"])
            text = " ".join(words_render)
            events.append(
                f"Dialogue: 0,{_fmt_time(max(0, w['start']))},{_fmt_time(w['end'])},Default,,0,0,0,,{text}"
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        f.write("\n".join(events))

    return output_path


def burn_subtitles(video_path: str, ass_path: str, output_path: str) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"ass={ass_path}",
        "-c:a", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
