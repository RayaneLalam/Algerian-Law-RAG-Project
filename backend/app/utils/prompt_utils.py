import os


def _load_prompt_template(path):
    """Load prompt template from file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading template: {e}")
        return """Tu es un assistant juridique expert en droit algérien. Réponds de manière précise, professionnelle et factuelle en te basant strictement sur le contexte fourni. Si l'information n'est pas dans le contexte, indique-le clairement.

Contexte juridique:
{context}

Question: {query}

Réponse:"""


def _format_context_from_results(results):
    """
    Format search results into a readable context block for the LLM.
    Each result contains a legal document with source type, header, and content.
    """
    if not results:
        return "Aucun contexte juridique disponible."

    context_parts = []

    for i, result in enumerate(results, start=1):
        # Extract the document from the result
        doc = result.get("document", {})

        # Get document metadata
        doc_type = doc.get("source_document_type", "DOCUMENT").upper()
        header = doc.get("header", "Sans titre")
        content = doc.get("content", "")

        # Get similarity score
        similarity = result.get("similarity", 0.0)

        # Format this document nicely
        doc_text = f"--- Document {i} ---\n"
        doc_text += f"Type: {doc_type}\n"
        doc_text += f"Référence: {header}\n"
        doc_text += f"Pertinence: {similarity:.3f}\n"
        doc_text += f"Contenu:\n{content}\n"

        context_parts.append(doc_text)

    return "\n".join(context_parts)
