"""API backend de Clip Factory: reçoit une URL, traite en tâche de fond,
expose le statut et les clips finaux. Auth via token Supabase.
"""
import os
import uuid
import traceback
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline.download import download_video
from pipeline.transcribe import transcribe
from pipeline.highlights import find_highlights
from pipeline.assemble import build_clip

import requests

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

app = FastAPI(title="Clip Factory API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("output", exist_ok=True)
os.makedirs("work", exist_ok=True)
os.makedirs("downloads", exist_ok=True)
app.mount("/files", StaticFiles(directory="output"), name="files")

# Store des jobs en mémoire. Suffisant pour un usage perso mono-instance.
# (si tu passes multi-instance un jour, remplace par une table Supabase)
JOBS: dict[str, dict] = {}


class JobRequest(BaseModel):
    url: str
    video_type: str = "podcast"
    n_clips: int = 3
    tracking_mode: str = "simple"


def get_user_id(authorization: str = Header(...)) -> str:
    """Vérifie le token Supabase en interrogeant directement l'API Supabase Auth."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token manquant")
    token = authorization.removeprefix("Bearer ")
    resp = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_ANON_KEY},
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(401, f"Token invalide: {resp.text}")
    return resp.json()["id"]


def run_pipeline(job_id: str, req: JobRequest):
    job = JOBS[job_id]
    try:
        job["status"] = "downloading"
        video_path, info = download_video(req.url, output_dir="downloads")
        job["title"] = info.get("title", "vidéo")

        job["status"] = "transcribing"
        transcript = transcribe(video_path)

        job["status"] = "analyzing"
        highlights = find_highlights(transcript["segments"], n=req.n_clips, video_type=req.video_type)

        job["status"] = "editing"
        job["total_clips"] = len(highlights)
        clips = []
        for i, h in enumerate(highlights, start=1):
            job["progress"] = i
            final_path = build_clip(
                source_path=video_path,
                highlight=h,
                words=transcript["words"],
                tracking_mode=req.tracking_mode,
                work_dir=f"work/{job_id}",
                final_output_dir=f"output/{job_id}",
                index=i,
            )
            clips.append({
                "title": h.get("title", f"Clip {i}"),
                "hook_score": h.get("hook_score"),
                "url": f"/files/{job_id}/{os.path.basename(final_path)}",
            })

        job["status"] = "done"
        job["clips"] = clips

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        job["traceback"] = traceback.format_exc()


@app.post("/jobs")
def create_job(req: JobRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_user_id)):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "id": job_id,
        "user_id": user_id,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "progress": 0,
        "total_clips": req.n_clips,
    }
    background_tasks.add_task(run_pipeline, job_id, req)
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, user_id: str = Depends(get_user_id)):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job introuvable")
    if job["user_id"] != user_id:
        raise HTTPException(403, "Accès refusé")
    return job


@app.get("/jobs")
def list_jobs(user_id: str = Depends(get_user_id)):
    return [j for j in JOBS.values() if j["user_id"] == user_id]


@app.get("/health")
def health():
    return {"status": "ok"}
