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




@chat_bp.route("/chat_stream", methods=["GET", "POST"])
@jwt_required
def chat_stream():
    """
    Protected endpoint.
    - Accepts message (POST JSON or GET query).
    - Optional conversation_id (JSON or query) to continue a conversation.
    - Optional model_version_id to specify which model to use.
    - Stores user message, streams assistant reply as SSE, saves assistant message after streaming.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    # get message + optional conversation_id + optional model_version_id
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if "message" not in data:
            return jsonify({"error": "Missing 'message' in JSON body"}), 400
        message = str(data["message"])
        conversation_id = data.get("conversation_id")
        model_version_id = data.get("model_version_id")
    else:
        message = request.args.get("message")
        if message is None:
            return jsonify({"error": "Missing 'message' query parameter"}), 400
        conversation_id = request.args.get("conversation_id")
        model_version_id = request.args.get("model_version_id")

    try:
        # Get default model version if none specified
        if not model_version_id:
            # Query for default model version
            default_model = current_app.db.execute(
                "SELECT id FROM model_versions WHERE is_default = 1 LIMIT 1"
            ).fetchone()
            if default_model:
                model_version_id = default_model["id"]
            else:
                # Fallback to any available model version
                any_model = current_app.db.execute(
                    "SELECT id FROM model_versions LIMIT 1"
                ).fetchone()
                if any_model:
                    model_version_id = any_model["id"]
                else:
                    return jsonify({"error": "No model versions available"}), 500

        # validate or create conversation
        if conversation_id:
            # conversation_id should be TEXT (UUID-like string) now, not int
            conv = chat_models.get_conversation_for_user(conversation_id, user_id)
            if not conv:
                return jsonify({"error": "Conversation not found or access denied"}), 404
        else:
            title = (message[:60] + "...") if len(message) > 60 else message
            conversation_id = chat_models.create_conversation(user_id, title=title)

        # store user message with model_version_id
        chat_models.insert_message(
            conversation_id, 
            role="user", 
            content=message,
            sender_user_id=user_id,
        )

        # Search for relevant articles
        top_k = 5  # Increased to get more context
        results = search_service.search(message, top_n=top_k)
        
        # Debug logging
        current_app.logger.info(f"Query: {message}")
        current_app.logger.info(f"Found {len(results)} results")
        current_app.logger.info(f"Using model version: {model_version_id}")
        
        for i, result in enumerate(results, 1):
            doc = result.get("document", {})
            current_app.logger.info(
                f"Result {i}: Article {doc.get('article', '?')} "
                f"(similarity: {result.get('similarity', 0):.3f}) - "
                f"Content preview: {doc.get('content', '')[:100]}"
            )
        
        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # Stream LLM reply (real response) with model_version_id
        return Response(
            stream_with_context(
                stream_assistant_reply(
                    message, 
                    vectors_json_str, 
                    conversation_id=conversation_id,
                    model_version_id=model_version_id
                )
            ),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        current_app.logger.exception("chat_stream error")
        return jsonify({"error": f"Server error: {e}"}), 500
    


