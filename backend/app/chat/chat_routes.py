import os
import json
import logging
from flask import request, jsonify, Response, stream_with_context, current_app, g
from . import chat_bp
from app.auth.auth_middleware import jwt_required
from .utils import stream_assistant_reply, stream_assistant_reply_demo
from . import chat_models
from ..services.language_service.language_service import LanguageService
from ..services.search_service.bilingual_search_service import BilingualSearchService

logger = logging.getLogger(__name__)

# Instantiate services
language_service = LanguageService()
search_service = BilingualSearchService()


@chat_bp.route("/chat_stream_demo", methods=["POST"])
def chat_stream_demo():
    """
    DEMO endpoint - No authentication required for testing.
    Same as /chat_stream but without JWT requirement.
    """
    print("chat_stream_demo called")
    data = request.get_json(silent=True) or {}
    if "message" not in data:
        return jsonify({"error": "Missing 'message' in JSON body"}), 400
    
    message = str(data["message"])
    language = data.get("language", 'auto')
    conversation_id = data.get("conversation_id")

    try:
        # Detect or normalize language
        if language == 'auto':
            language = language_service.detect_response_language(message)
        else:
            language = language_service.normalize_language(language)
        
        logger.info(f"[DEMO] Processing query in language: {language}")
        
        # Search documents in appropriate language
        top_k = 3
        results = search_service.search(message, language=language, top_k=top_k)
        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # Return SSE response from bilingual service (demo - no DB save)
        return Response(
            stream_with_context(stream_assistant_reply_demo(message, vectors_json_str, language=language)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Language": language
            }
        )
    except Exception as e:
        logger.exception("chat_stream_demo error")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@chat_bp.route("/chat_stream", methods=["GET", "POST"])
@jwt_required
def chat_stream():
    """
    Protected bilingual chat endpoint.
    - Accepts message (POST JSON or GET query).
    - Optional conversation_id (JSON or query) to continue a conversation.
    - Optional language parameter to specify response language.
    - Detects language automatically if not specified.
    - Stores user message, streams assistant reply as SSE, saves assistant message after streaming.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    # Get message, optional conversation_id, and optional language
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if "message" not in data:
            return jsonify({"error": "Missing 'message' in JSON body"}), 400
        message = str(data["message"])
        conversation_id = data.get("conversation_id")
        language = data.get("language", 'auto')
    else:
        message = request.args.get("message")
        if message is None:
            return jsonify({"error": "Missing 'message' query parameter"}), 400
        conversation_id = request.args.get("conversation_id")
        language = request.args.get("language", 'auto')

    try:
        # Detect or normalize language
        if language == 'auto':
            language = language_service.detect_response_language(message)
        else:
            language = language_service.normalize_language(language)
        
        logger.info(f"Processing query in language: {language}")
        
        # Validate or create conversation
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

        # Store user message with language metadata
        chat_models.insert_message(conversation_id, "user", message)

        # Search documents in appropriate language
        top_k = 3
        results = search_service.search(message, language=language, top_k=top_k)
        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # Return SSE response from bilingual service
        return Response(
            stream_with_context(stream_assistant_reply(message, vectors_json_str, conversation_id, language=language)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Language": language
            }
        )
    except Exception as e:
        logger.exception("chat_stream error")
        return jsonify({"error": f"Server error: {e}"}), 500