import os
import logging

logger = logging.getLogger(__name__)


def _load_prompt_template(path: str) -> str:
    """Load prompt template from file with fallback."""
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
                    logger.warning(f"Template at {path} missing placeholders, using default")
                    return default_template
                return txt
        else:
            logger.warning(f"Template not found at {path}, using default")
            return default_template
    except Exception as e:
        logger.error(f"Error loading template from {path}: {e}")
        return default_template


def load_language_prompt_template(language: str) -> str:
    """Load language-specific prompt template."""
    language = language.lower().strip()
    if language in ('ar', 'arabic', 'العربية'):
        path = './app/prompt_templates/qa_with_context_ar.txt'
    else:
        path = './app/prompt_templates/qa_with_context_fr.txt'
    
    return _load_prompt_template(path)


def _format_context_from_results(results, language: str = 'fr'):
    """Format context from search results with language awareness."""
    lines = []
    language = language.lower().strip()
    
    for i, r in enumerate(results, start=1):
        doc = r.get("document") if isinstance(r, dict) and r.get("document") else r
        
        if isinstance(doc, dict):
            # Language-aware field selection
            if language in ('ar', 'arabic', 'العربية'):
                titre = doc.get("titre") or doc.get("title") or f"وثيقة_{i}"
                texte = doc.get("texte") or doc.get("text") or ""
            else:
                titre = doc.get("header") or doc.get("titre") or doc.get("title") or f"doc_{i}"
                texte = doc.get("content") or doc.get("texte") or doc.get("text") or ""
        else:
            titre = f"doc_{i}"
            texte = str(doc)
        
        score = r.get("score", None)
        score_str = f" (score={score:.4f})" if isinstance(score, (float, int)) else ""
        
        short_text = texte.strip().replace("\n", " ")
        if len(short_text) > 400:
            short_text = short_text[:390].rstrip() + "..."
        
        lines.append(f"{i}. {titre} — {short_text}{score_str}")
    
    if not lines:
        return "No context found." if language not in ('ar', 'arabic', 'العربية') else "لم يتم العثور على سياق."
    
    return "\n".join(lines)
