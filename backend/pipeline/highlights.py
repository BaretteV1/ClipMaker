"""Envoie la transcription à Gemini (gratuit, tier généreux) pour identifier les meilleurs extraits."""
import json
import os
import google.generativeai as genai

SYSTEM_PROMPT = """Tu es un monteur expert en contenu viral pour TikTok / Reels / YouTube Shorts.
On te donne la transcription complète d'une vidéo (podcast, reportage ou combat/sport), avec les
timestamps en secondes de chaque segment de parole.

Ta mission: repérer les {n} MEILLEURS extraits à découper pour en faire des clips verticaux.

Critères de sélection (par ordre d'importance):
1. Le moment doit avoir un "hook" fort dans les 3 premières secondes (question choc, punchline,
   révélation, moment de tension ou d'action).
2. L'extrait doit être compréhensible SEUL, sans le contexte du reste de la vidéo.
3. Il doit avoir un vrai arc: un début qui accroche, un développement, une chute ou un climax.
4. Durée: entre 20 et 90 secondes.
5. Ne coupe jamais au milieu d'une phrase: les bornes start/end doivent tomber sur des frontières
   naturelles de phrase.
6. Si c'est un contenu de combat/sport, privilégie les moments d'action, de KO, de retournement.
7. Si c'est un podcast/reportage, privilégie les punchlines, anecdotes fortes, débats, révélations.

Réponds STRICTEMENT en JSON valide, sans aucun texte autour, format:
[
  {{"start": 123.4, "end": 178.9, "title": "titre court accrocheur", "reason": "pourquoi ce moment marche", "hook_score": 8}}
]
hook_score est une note de 1 à 10 sur le potentiel viral. Trie la liste du meilleur au moins bon score.
"""


def find_highlights(segments: list[dict], n: int = 5, video_type: str = "podcast") -> list[dict]:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    # gemini-2.5-flash: gratuit sur le tier free (rate-limité). Si Google le déprécie,
    # remplace par le dernier modèle "flash" gratuit listé sur ai.google.dev/gemini-api/docs/pricing
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT.format(n=n),
    )

    transcript_text = "\n".join(
        f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments
    )

    user_prompt = (
        f"Type de vidéo: {video_type}\n\n"
        f"Transcription (timestamps en secondes):\n{transcript_text}"
    )

    resp = model.generate_content(
        user_prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.4),
    )

    content = resp.text.strip()
    # Nettoyage au cas où le modèle entoure sa réponse de ```json ... ```
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        highlights = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Réponse Groq non-JSON: {content[:500]}") from e

    return highlights
