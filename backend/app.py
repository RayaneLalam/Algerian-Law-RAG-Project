# app.py
import os
import json
from flask import Flask, request, jsonify, Response, stream_with_context
from search_service.search_service import SearchService  # direct import of your SearchService
from llm_service.llm_api import LLM_Service  # direct import of the LLM wrapper

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False   # << add this

# Globals: instantiate services once
search_service = SearchService()
llm_service = LLM_Service()

# Prompt template path
PROMPT_TEMPLATE_PATH = os.path.join(".", "prompt_templates", "qa_with_context.txt")


def _load_prompt_template(path: str) -> str:
    """
    Load the prompt template from disk. If missing or unreadable, return a safe default template.
    The template must contain {query} and {context} placeholders.
    """
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
                # Ensure placeholders exist (basic validation)
                if "{query}" not in txt or "{context}" not in txt:
                    return default_template
                return txt
        else:
            return default_template
    except Exception:
        return default_template


def _format_context_from_results(results):
    """
    Given search results (list of dicts), produce a human-friendly numbered context block.
    Expects each result item to have either:
      - a 'document' field with dict containing 'titre' and 'texte', OR
      - the result itself to be a dict with 'titre' and 'texte'.
    Also uses 'similarity' (if present) for informative display.
    """
    lines = []
    for i, r in enumerate(results, start=1):
        # r could be a dict result returned by SearchService._vector_search:
        # { "index": int, "distance": ..., "similarity": ..., "document": {...} }
        doc = r.get("document") if isinstance(r, dict) and r.get("document") else r
        if isinstance(doc, dict):
            titre = doc.get("titre") or doc.get("title") or f"doc_{r.get('index', i-1)}"
            texte = doc.get("texte") or doc.get("text") or ""
        else:
            titre = f"doc_{i}"
            texte = str(doc)

        sim = r.get("similarity", None) if isinstance(r, dict) else None
        sim_str = f" (sim={sim:.4f})" if isinstance(sim, (float, int)) else ""
        # Shorten text for readability (but keep meaningful amount)
        short_text = texte.strip().replace("\n", " ")
        if len(short_text) > 400:
            short_text = short_text[:390].rstrip() + "…"

        lines.append(f"{i}. {titre} — {short_text}{sim_str}")
    if not lines:
        return "Aucun contexte trouvé."
    return "\n".join(lines)


def make_reply(received_message: str, vectors_json_str: str) -> str:
    """
    Build a prompt from the template using the received message and the retrieved vectors,
    then call the LLM_Service and return the model's response (string).
    """
    # 1) Parse the vectors JSON string into objects
    try:
        results = json.loads(vectors_json_str) if vectors_json_str else []
    except Exception:
        # fallback: empty list if parsing fails
        results = []

    # 2) Build a formatted context string (numbered list)
    context_block = _format_context_from_results(results)

    # 3) Load template
    template = _load_prompt_template(PROMPT_TEMPLATE_PATH)

    # 4) Fill template with query and context
    try:
        prompt = template.format(query=received_message, context=context_block)
    except Exception:
        # If formatting fails, fall back to a simple concatenation
        prompt = f"Question: {received_message}\n\nContext:\n{context_block}"

    # 5) Call LLM_Service (send prompt as-is)
    try:
        llm_response = llm_service.get_completion(prompt)
    except Exception as e:
        # Return an error-style message that still follows the previous "dummy" pattern
        return f"Error contacting LLM: {e}"

    # 6) Return the LLM response (string)
    return llm_response


@app.route("/chat", methods=["GET", "POST"])
def chat():
    # Accept message via JSON POST {"message": "..."} or GET ?message=...
    if request.method == "POST":
        data = request.get_json(silent=True)
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' in JSON body"}), 400
        message = str(data["message"])
    else:
        message = request.args.get("message")
        if message is None:
            return jsonify({"error": "Missing 'message' query parameter"}), 400

    try:
        top_k = 3
        results = search_service.search(message, top_n=top_k)
        vectors_json_str = json.dumps(results, ensure_ascii=False)
        reply = make_reply(message, vectors_json_str)
        return jsonify({"reply": reply}), 200
    except Exception as e:
        return jsonify({"error": f"Server error during search or LLM call: {e}"}), 500
    





def make_reply_stream(received_message: str, vectors_json_str: str):
    """
    Build a prompt and return a generator that streams the LLM response.
    """
    try:
        results = json.loads(vectors_json_str) if vectors_json_str else []
    except Exception:
        results = []

    context_block = _format_context_from_results(results)
    template = _load_prompt_template(PROMPT_TEMPLATE_PATH)

    try:
        prompt = template.format(query=received_message, context=context_block)
    except Exception:
        prompt = f"Question: {received_message}\n\nContext:\n{context_block}"

    # Return the streaming generator
    return llm_service.get_completion_stream(prompt)



@app.route("/chat_stream", methods=["GET", "POST"])
def chat_stream():
    if request.method == "POST":
        data = request.get_json(silent=True)
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' in JSON body"}), 400
        message = str(data["message"])
    else:
        message = request.args.get("message")
        if message is None:
            return jsonify({"error": "Missing 'message' query parameter"}), 400

    try:
        top_k = 3
        results = search_service.search(message, top_n=top_k)
        vectors_json_str = json.dumps(results, ensure_ascii=False)
        
        def generate():
            for chunk in make_reply_stream(message, vectors_json_str):
                # Send each chunk as JSON
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500










if __name__ == "__main__":
    # For development only — use a proper WSGI server in production.
    app.run(host="0.0.0.0", port=5000, debug=True)
