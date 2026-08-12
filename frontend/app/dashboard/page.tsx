"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase, API_URL } from "@/lib/supabaseClient";

type Clip = { title: string; hook_score: number | null; url: string };
type Job = {
  id: string;
  status: "queued" | "downloading" | "transcribing" | "analyzing" | "editing" | "done" | "error";
  title?: string;
  progress?: number;
  total_clips?: number;
  clips?: Clip[];
  error?: string;
};

const STATUS_LABEL: Record<Job["status"], string> = {
  queued: "En file d'attente…",
  downloading: "Téléchargement de la vidéo…",
  transcribing: "Transcription en cours…",
  analyzing: "Recherche des meilleurs moments…",
  editing: "Montage des clips…",
  done: "Terminé",
  error: "Erreur",
};

export default function Dashboard() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [inputMode, setInputMode] = useState<"url" | "upload">("url");
  const [videoType, setVideoType] = useState("podcast");
  const [nClips, setNClips] = useState(3);
  const [trackingMode, setTrackingMode] = useState("simple");
  const [job, setJob] = useState<Job | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) router.replace("/login");
      else setChecking(false);
    });
  }, [router]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  async function authHeader() {
    const { data } = await supabase.auth.getSession();
    return { Authorization: `Bearer ${data.session?.access_token}` };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    setJob(null);

    try {
      const headers = await authHeader();
      let res: Response;

      if (inputMode === "upload") {
        if (!file) throw new Error("Choisis un fichier vidéo.");
        const form = new FormData();
        form.append("file", file);
        form.append("video_type", videoType);
        form.append("n_clips", String(nClips));
        form.append("tracking_mode", trackingMode);
        res = await fetch(`${API_URL}/jobs/upload`, { method: "POST", headers, body: form });
      } else {
        res = await fetch(`${API_URL}/jobs`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...headers },
          body: JSON.stringify({ url, video_type: videoType, n_clips: nClips, tracking_mode: trackingMode }),
        });
      }

      if (!res.ok) throw new Error(await res.text());
      const { job_id } = await res.json();
      setJob({ id: job_id, status: "queued" });
      startPolling(job_id);
    } catch (err: any) {
      // Cas fréquent: le backend Render gratuit s'était mis en veille -> premier appel lent/échoue
      setSubmitError(
        "Le serveur ne répond pas (il se réveille peut-être — réessaie dans 30-60 secondes) : " + err.message
      );
    }
  }

  function startPolling(jobId: string) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const headers = await authHeader();
      const res = await fetch(`${API_URL}/jobs/${jobId}`, { headers });
      if (!res.ok) return;
      const data: Job = await res.json();
      setJob(data);
      if (data.status === "done" || data.status === "error") {
        clearInterval(pollRef.current!);
      }
    }, 4000);
  }

  async function handleLogout() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  if (checking) {
    return <div className="min-h-screen flex items-center justify-center text-reel-dim text-sm">Chargement…</div>;
  }

  return (
    <div className="min-h-screen px-6 py-8 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-10">
        <div>
          <p className="text-reel-amber text-xs tracking-[0.3em] mb-1">REC ●</p>
          <h1 className="font-display text-2xl font-bold text-reel-text">CLIP FACTORY</h1>
        </div>
        <button onClick={handleLogout} className="text-reel-dim text-xs underline underline-offset-4">
          Déconnexion
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 border border-reel-line bg-reel-panel p-5 mb-8">
        <div>
          <div className="flex gap-2 mb-2">
            <button
              type="button"
              onClick={() => setInputMode("url")}
              className={`text-xs px-3 py-1 border ${inputMode === "url" ? "border-reel-amber text-reel-amber" : "border-reel-line text-reel-dim"}`}
            >
              URL
            </button>
            <button
              type="button"
              onClick={() => setInputMode("upload")}
              className={`text-xs px-3 py-1 border ${inputMode === "upload" ? "border-reel-amber text-reel-amber" : "border-reel-line text-reel-dim"}`}
            >
              Fichier
            </button>
          </div>

          {inputMode === "url" ? (
            <>
              <label className="block text-xs text-reel-dim mb-1 tracking-wide">URL DE LA VIDÉO</label>
              <input
                type="url"
                required={inputMode === "url"}
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-reel-bg border border-reel-line px-3 py-2 text-sm focus:outline-none focus:border-reel-amber"
              />
            </>
          ) : (
            <>
              <label className="block text-xs text-reel-dim mb-1 tracking-wide">FICHIER VIDÉO</label>
              <input
                type="file"
                accept="video/*"
                required={inputMode === "upload"}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full bg-reel-bg border border-reel-line px-3 py-2 text-sm file:mr-3 file:bg-reel-line file:text-reel-text file:border-0 file:px-2 file:py-1"
              />
            </>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-reel-dim mb-1 tracking-wide">TYPE</label>
            <select
              value={videoType}
              onChange={(e) => setVideoType(e.target.value)}
              className="w-full bg-reel-bg border border-reel-line px-3 py-2 text-sm focus:outline-none focus:border-reel-amber"
            >
              <option value="podcast">Podcast</option>
              <option value="reportage">Reportage</option>
              <option value="combat">Combat</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-reel-dim mb-1 tracking-wide">RECADRAGE</label>
            <select
              value={trackingMode}
              onChange={(e) => setTrackingMode(e.target.value)}
              className="w-full bg-reel-bg border border-reel-line px-3 py-2 text-sm focus:outline-none focus:border-reel-amber"
            >
              <option value="simple">Simple (rapide)</option>
              <option value="advanced">Avancé (tracking)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs text-reel-dim mb-1 tracking-wide">
            NOMBRE DE CLIPS: {nClips}
          </label>
          <input
            type="range"
            min={1}
            max={8}
            value={nClips}
            onChange={(e) => setNClips(Number(e.target.value))}
            className="w-full accent-reel-amber"
          />
        </div>

        {submitError && <p className="text-reel-rec text-xs">{submitError}</p>}

        <button
          type="submit"
          disabled={job !== null && job.status !== "done" && job.status !== "error"}
          className="w-full bg-reel-amber text-reel-bg font-display font-bold py-2.5 text-sm tracking-wide hover:bg-reel-amberDim disabled:opacity-50 transition-colors"
        >
          GÉNÉRER LES CLIPS
        </button>
      </form>

      {job && (
        <div className="border border-reel-line bg-reel-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-reel-text">{job.title || "Traitement en cours"}</p>
            <span className={`text-xs ${job.status === "error" ? "text-reel-rec" : "text-reel-amber"}`}>
              {STATUS_LABEL[job.status]}
            </span>
          </div>

          {job.status === "editing" && job.total_clips ? (
            <p className="text-xs text-reel-dim mb-3">
              Clip {job.progress ?? 0} / {job.total_clips}
            </p>
          ) : null}

          {job.status === "error" && (
            <p className="text-xs text-reel-rec">{job.error}</p>
          )}

          {job.status === "done" && job.clips && (
            <ul className="space-y-2 mt-3">
              {job.clips.map((c, i) => (
                <li key={i} className="flex items-center justify-between border-t border-reel-line pt-2">
                  <div>
                    <p className="text-sm text-reel-text">{c.title}</p>
                    {c.hook_score != null && (
                      <p className="text-xs text-reel-dim">score {c.hook_score}/10</p>
                    )}
                  </div>
                  <a
                    href={`${API_URL}${c.url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-reel-amber text-xs underline underline-offset-4"
                  >
                    Télécharger
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
