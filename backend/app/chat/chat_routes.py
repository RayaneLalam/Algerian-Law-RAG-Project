import os
import json
from flask import request, jsonify, Response, stream_with_context, current_app, g
from ..services.search_service.search_service import SearchService
from . import chat_bp
from app.auth.auth_middleware import jwt_required
from .utils import stream_assistant_reply
from . import chat_models

# Instantiate services globally
search_service = SearchService()



# def make_reply(received_message: str, vectors_json_str: str) -> str:
#     try:
#         results = json.loads(vectors_json_str) if vectors_json_str else []
#     except Exception:
#         results = []

#     context_block = _format_context_from_results(results)
#     template = _load_prompt_template(PROMPT_TEMPLATE_PATH)

#     try:
#         prompt = template.format(query=received_message, context=context_block)
#     except Exception:
#         prompt = f"Question: {received_message}\n\nContext:\n{context_block}"

#     try:
#         llm_response = llm_service.get_completion(prompt)
#     except Exception as e:
#         return f"Error contacting LLM: {e}"

#     return llm_response


# @chat_bp.route("/chat", methods=["GET", "POST"])
# def chat():
#     if request.method == "POST":
#         data = request.get_json(silent=True)
#         if not data or "message" not in data:
#             return jsonify({"error": "Missing 'message' in JSON body"}), 400
#         message = str(data["message"])
#     else:
#         message = request.args.get("message")
#         if message is None:
#             return jsonify({"error": "Missing 'message' query parameter"}), 400

#     try:
#         top_k = 3
#         results = search_service.search(message, top_n=top_k)
#         vectors_json_str = json.dumps(results, ensure_ascii=False)
#         reply = make_reply(message, vectors_json_str)
#         return jsonify({"reply": reply}), 200
#     except Exception as e:
#         return jsonify({"error": f"Server error during search or LLM call: {e}"}), 500




@chat_bp.route("/chat_stream", methods=["GET", "POST"])
@jwt_required
def chat_stream():
    """
    Protected endpoint.
    - Accepts message (POST JSON or GET query).
    - Optional conversation_id (JSON or query) to continue a conversation.
    - Stores user message, streams assistant reply as SSE, saves assistant message after streaming.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    # get message + optional conversation_id
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if "message" not in data:
            return jsonify({"error": "Missing 'message' in JSON body"}), 400
        message = str(data["message"])
        conversation_id = data.get("conversation_id")
    else:
        message = request.args.get("message")
        if message is None:
            return jsonify({"error": "Missing 'message' query parameter"}), 400
        conversation_id = request.args.get("conversation_id")

    try:
        # validate or create conversation
        if conversation_id:
            try:
                conversation_id = int(conversation_id)
            except Exception:
                return jsonify({"error": "Invalid conversation_id"}), 400
            conv = chat_models.get_conversation_for_user(conversation_id, user_id)
            if not conv:
                return jsonify({"error": "Conversation not found or access denied"}), 404
        else:
            title = (message[:60] + "...") if len(message) > 60 else message
            conversation_id = chat_models.create_conversation(user_id, title=title)

        # store user message
        chat_models.insert_message(conversation_id, "user", message)

        # prepare context
        top_k = 3
        results = search_service.search(message, top_n=top_k)
        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # return SSE response coming from service
        return Response(
            stream_with_context(stream_assistant_reply(message, vectors_json_str, conversation_id)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        current_app.logger.exception("chat_stream error")
        return jsonify({"error": f"Server error: {e}"}), 500