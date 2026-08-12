"""Recadre un clip en 9:16 vertical.

Mode "simple": crop centré fixe (rapide, marche bien si le sujet ne bouge pas trop).
Mode "advanced": suit le(s) visage(s) frame par frame et fait bouger le crop pour
                  garder le sujet centré (utile pour du combat / de l'action).
"""
import subprocess
import cv2
import numpy as np

TARGET_RATIO = 9 / 16  # largeur / hauteur


def _probe_size(video_path: str) -> tuple[int, int]:
    import ffmpeg
    probe = ffmpeg.probe(video_path)
    stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    return int(stream["width"]), int(stream["height"])


def crop_simple(input_path: str, output_path: str) -> None:
    """Crop centré fixe en 9:16, encodé directement avec ffmpeg (rapide)."""
    w, h = _probe_size(input_path)
    target_w = int(h * TARGET_RATIO)
    if target_w > w:
        target_w = w
    x_offset = (w - target_w) // 2

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"crop={target_w}:{h}:{x_offset}:0,scale=1080:1920",
        "-c:a", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _detect_face_centers(video_path: str, sample_every_n_frames: int = 5) -> list[tuple[float, float]]:
    """Retourne une liste de centres x (normalisés 0-1) échantillonnés dans le temps."""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    centers = []  # (timestamp_sec, x_normalized)
    idx = 0
    last_center = 0.5
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % sample_every_n_frames == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            if len(faces) > 0:
                # prend le plus gros visage détecté (probablement le sujet principal)
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                cx = (fx + fw / 2) / width
                last_center = cx
            centers.append((idx / fps, last_center))
        idx += 1
    cap.release()
    return centers


def _smooth_centers(centers: list[tuple[float, float]], window: int = 7) -> list[tuple[float, float]]:
    if not centers:
        return centers
    xs = np.array([c[1] for c in centers])
    kernel = np.ones(window) / window
    smoothed = np.convolve(xs, kernel, mode="same")
    return [(centers[i][0], float(smoothed[i])) for i in range(len(centers))]


def crop_advanced(input_path: str, output_path: str) -> None:
    """Crop dynamique qui suit le visage principal. Plus lent que le mode simple."""
    w, h = _probe_size(input_path)
    target_w = int(h * TARGET_RATIO)
    if target_w > w:
        crop_simple(input_path, output_path)
        return

    raw_centers = _detect_face_centers(input_path)
    centers = _smooth_centers(raw_centers)

    if not centers:
        crop_simple(input_path, output_path)
        return

    # Construit une expression ffmpeg 'sendcmd' pour faire bouger le crop x dans le temps.
    # On limite le nombre de points de contrôle pour garder une commande raisonnable.
    max_points = 200
    step = max(1, len(centers) // max_points)
    sampled = centers[::step]

    cmd_lines = []
    for t, cx in sampled:
        x_pixel = int(max(0, min(w - target_w, cx * w - target_w / 2)))
        cmd_lines.append(f"{t:.2f} crop x {x_pixel};")
    sendcmd_script = "\n".join(cmd_lines)

    script_path = output_path + ".sendcmd.txt"
    with open(script_path, "w") as f:
        f.write(sendcmd_script)

    first_x = int(max(0, min(w - target_w, sampled[0][1] * w - target_w / 2)))
    vf = (
        f"sendcmd=f={script_path},"
        f"crop=w={target_w}:h={h}:x={first_x}:y=0,"
        f"scale=1080:1920"
    )

    cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", vf, "-c:a", "copy", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
