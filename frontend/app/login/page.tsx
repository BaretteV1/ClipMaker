"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirmSent, setConfirmSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const { error } =
      mode === "signin"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }
    if (mode === "signup") {
      setConfirmSent(true);
      return;
    }
    router.replace("/dashboard");
  }

  return (
    <div className="min-h-screen flex">
      {/* Rail perforée façon pellicule 35mm */}
      <div className="hidden sm:flex flex-col justify-between py-8 px-3 border-r border-reel-line">
        {Array.from({ length: 14 }).map((_, i) => (
          <div key={i} className="w-2 h-2 rounded-sm bg-reel-line" />
        ))}
      </div>

      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <div className="mb-10">
            <p className="text-reel-amber text-xs tracking-[0.3em] mb-2">REC ●</p>
            <h1 className="font-display text-3xl font-bold text-reel-text">CLIP FACTORY</h1>
            <p className="text-reel-dim text-sm mt-2">
              Colle une vidéo. Récupère tes meilleurs moments, montés, verticaux, sous-titrés.
            </p>
          </div>

          {confirmSent ? (
            <div className="border border-reel-line bg-reel-panel p-4 text-sm text-reel-text">
              Compte créé. Vérifie ta boîte mail pour confirmer ton adresse, puis reviens te connecter.
              <button
                onClick={() => { setConfirmSent(false); setMode("signin"); }}
                className="block mt-3 text-reel-amber underline underline-offset-4"
              >
                Retour à la connexion
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs text-reel-dim mb-1 tracking-wide">EMAIL</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-reel-panel border border-reel-line px-3 py-2 text-reel-text text-sm focus:outline-none focus:border-reel-amber"
                />
              </div>
              <div>
                <label className="block text-xs text-reel-dim mb-1 tracking-wide">MOT DE PASSE</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-reel-panel border border-reel-line px-3 py-2 text-reel-text text-sm focus:outline-none focus:border-reel-amber"
                />
              </div>

              {error && <p className="text-reel-rec text-xs">{error}</p>}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-reel-amber text-reel-bg font-display font-bold py-2.5 text-sm tracking-wide hover:bg-reel-amberDim disabled:opacity-50 transition-colors"
              >
                {loading ? "…" : mode === "signin" ? "SE CONNECTER" : "CRÉER LE COMPTE"}
              </button>

              <button
                type="button"
                onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
                className="w-full text-reel-dim text-xs underline underline-offset-4"
              >
                {mode === "signin" ? "Pas encore de compte ? Créer un compte" : "Déjà un compte ? Se connecter"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
