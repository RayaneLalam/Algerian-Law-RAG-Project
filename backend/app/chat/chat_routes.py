import os
import json
from flask import request, jsonify, Response, stream_with_context
from ..services.search_service.search_service import SearchService
from ..services.llm_service.llm_api import LLM_Service
from ..utils.prompt_utils import _load_prompt_template, _format_context_from_results
from . import chat_bp
from app.auth.auth_middleware import jwt_required

#chat_bp = Blueprint("chat", __name__)

# Instantiate services globally
search_service = SearchService()
llm_service = LLM_Service()

PROMPT_TEMPLATE_PATH = os.path.join(".", "app", "prompt_templates", "qa_with_context.txt")


def make_reply(received_message: str, vectors_json_str: str) -> str:
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

    try:
        llm_response = llm_service.get_completion(prompt)
    except Exception as e:
        return f"Error contacting LLM: {e}"

    return llm_response


@chat_bp.route("/chat", methods=["GET", "POST"])
def chat():
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

    return llm_service.get_completion_stream(prompt)


@chat_bp.route("/chat_stream", methods=["GET", "POST"])
@jwt_required
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
