import os

def _load_prompt_template(path: str) -> str:
    default_template = (
        "You are a helpful assistant.\n\n"
        "User question:\n{query}\n\n"
        "Context:\n{context}\n\n"
        "Answer concisely using the context when possible.\n"
    )
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
                if "{query}" not in txt or "{context}" not in txt:
                    return default_template
                return txt
        else:
            return default_template
    except Exception:
        return default_template


def _format_context_from_results(results):
    lines = []
    for i, r in enumerate(results, start=1):
        doc = r.get("document") if isinstance(r, dict) and r.get("document") else r
        if isinstance(doc, dict):
            titre = doc.get("titre") or doc.get("title") or f"doc_{r.get('index', i-1)}"
            texte = doc.get("texte") or doc.get("text") or ""
        else:
            titre = f"doc_{i}"
            texte = str(doc)

        sim = r.get("similarity", None) if isinstance(r, dict) else None
        sim_str = f" (sim={sim:.4f})" if isinstance(sim, (float, int)) else ""
        short_text = texte.strip().replace("\n", " ")
        if len(short_text) > 400:
            short_text = short_text[:390].rstrip() + "…"

        lines.append(f"{i}. {titre} — {short_text}{sim_str}")
    if not lines:
        return "Aucun contexte trouvé."
    return "\n".join(lines)
