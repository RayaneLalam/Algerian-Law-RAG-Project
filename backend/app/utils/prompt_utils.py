import os

def _load_prompt_template(path):
    """Load prompt template from file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading template: {e}")
        return "Question: {query}\n\nContext:\n{context}\n\nAnswer:"


def _format_context_from_results(results):
    """
    Format search results into a readable context block for the LLM.
    Each result should contain: document with article content, reference, etc.
    """
    if not results:
        return "Aucun contexte disponible."
    
    context_parts = []
    
    for i, result in enumerate(results, start=1):
        # Extract the document from the result
        doc = result.get("document", {})
        
        # Get article metadata
        title = doc.get("title", "?")
        chapter = doc.get("chapter", "?")
        article = doc.get("article", "?")
        title_name = doc.get("title_name", "")
        chapter_name = doc.get("chapter_name", "")
        content = doc.get("content", "")
        
        # Get similarity score
        similarity = result.get("similarity", 0.0)
        
        # Format this article nicely
        article_text = f"[Article {i}]\n"
        article_text += f"Référence: Titre {title}"
        if title_name:
            article_text += f" ({title_name})"
        article_text += f", Chapitre {chapter}"
        if chapter_name:
            article_text += f" ({chapter_name})"
        article_text += f", Article {article}\n"
        article_text += f"Pertinence: {similarity:.3f}\n"
        article_text += f"Contenu:\n{content}\n"
        
        context_parts.append(article_text)
    
    return "\n".join(context_parts)