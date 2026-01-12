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

# Global service instances (lazy loaded)
_language_service = None
_search_service = None

def get_language_service():
    """Get or create the singleton language service."""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service

def get_search_service():
    """Get or create the singleton search service."""
    global _search_service
    if _search_service is None:
        _search_service = BilingualSearchService()
    return _search_service

# ============================================================================
# CONVERSATION MANAGEMENT ENDPOINTS (Authenticated)
# ============================================================================

@chat_bp.route("/conversations", methods=["GET"])
@jwt_required
def get_conversations():
    """
    Get all conversations for the authenticated user.
    Returns conversations sorted by most recent first.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    try:
        conversations = chat_models.get_all_conversations_for_user(user_id)

        result = []
        for conv in conversations:
            result.append({
                "id": str(conv["id"]),
                "title": conv["title"],
                "status": conv["status"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "message_count": conv["message_count"]
            })

        return jsonify({"conversations": result}), 200

    except Exception as e:
        current_app.logger.exception("Error fetching conversations")
        return jsonify({"error": f"Server error: {e}"}), 500


@chat_bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@jwt_required
def get_conversation_messages(conversation_id):
    """
    Get all messages for a specific conversation.
    Only returns messages if user owns the conversation.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    try:
        messages = chat_models.get_conversation_messages(conversation_id, user_id)

        if messages is None:
            return jsonify({"error": "Conversation not found or access denied"}), 404

        result = []
        for msg in messages:
            result.append({
                "id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "tokens": msg["tokens"],
                "created_at": msg["created_at"]
            })

        return jsonify({"messages": result}), 200

    except Exception as e:
        current_app.logger.exception("Error fetching messages")
        return jsonify({"error": f"Server error: {e}"}), 500


@chat_bp.route("/conversations", methods=["POST"])
@jwt_required
def create_conversation():
    """
    Create a new conversation.
    Expects JSON body with optional 'title'.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    try:
        data = request.get_json(silent=True) or {}
        title = data.get("title", "New Conversation")

        conversation_id = chat_models.create_conversation(user_id, title=title)

        return jsonify({
            "conversation_id": str(conversation_id),
            "title": title,
            "created_at": None  # Will be set by database
        }), 201

    except Exception as e:
        current_app.logger.exception("Error creating conversation")
        return jsonify({"error": f"Server error: {e}"}), 500


@chat_bp.route("/conversations/<int:conversation_id>", methods=["DELETE"])
@jwt_required
def delete_conversation(conversation_id):
    """
    Soft delete a conversation (set status to 'deleted').
    Only allows deletion if user owns the conversation.
    """
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    user_id = user["id"]

    try:
        success = chat_models.delete_conversation(conversation_id, user_id)

        if not success:
            return jsonify({"error": "Conversation not found or access denied"}), 404

        return jsonify({"message": "Conversation deleted successfully"}), 200

    except Exception as e:
        current_app.logger.exception("Error deleting conversation")
        return jsonify({"error": f"Server error: {e}"}), 500


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@chat_bp.route("/chat_stream_demo", methods=["POST"])
def chat_stream_demo():
    """
    DEMO endpoint - No authentication required for testing.
    Uses the working logic for language detection and search.
    """
    print("chat_stream_demo called")
    data = request.get_json(silent=True) or {}
    if "message" not in data:
        return jsonify({"error": "Missing 'message' in JSON body"}), 400
    
    message = str(data["message"])
    language = data.get("language", 'auto')
    # conversation_id is optional for demo
    
    try:
        # 1. Detect or normalize language
        lang_service = get_language_service()
        if language == 'auto':
            language = lang_service.detect_response_language(message)
        else:
            language = lang_service.normalize_language(language)
        
        logger.info(f"[DEMO] Processing query in language: {language}")
        
        # 2. Search documents in appropriate language
        top_k = 3
        srch_service = get_search_service()
        results = srch_service.search(message, language=language, top_k=top_k)
        
        # Debug log for results
        logger.info(f"[DEMO] Found {len(results)} results")
        
        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # 3. Return SSE response (using demo utility)
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
    - Enforces Authentication (@jwt_required).
    - Uses the exact same Language/Search logic as the working demo.
    - Saves conversation history to the database.
    """
    try:
        user = getattr(g, "current_user", None)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        user_id = user["id"]

        # 1. Parse Input
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
            
        logger.info(f"Processing authenticated query for user {user_id}")
        
        # 2. Detect or normalize language (Same logic as Demo)
        lang_service = get_language_service()
        if language == 'auto':
            language = lang_service.detect_response_language(message)
        else:
            language = lang_service.normalize_language(language)
        
        logger.info(f"Language detected/normalized: {language}")
        
        # 3. Manage Conversation (DB Logic)
        if conversation_id:
            try:
                conversation_id = int(conversation_id)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid conversation_id format"}), 400

            conv = chat_models.get_conversation_for_user(conversation_id, user_id)
            if not conv:
                return jsonify({"error": "Conversation not found or access denied"}), 404
        else:
            # Create new conversation if ID not provided
            title = (message[:60] + "...") if len(message) > 60 else message
            conversation_id = chat_models.create_conversation(user_id, title=title)

        # 4. Store User Message
        chat_models.insert_message(
            conversation_id,
            role="user",
            content=message,
            sender_user_id=user_id,
        )

        # 5. Search Documents (Same logic as Demo)
        top_k = 3
        srch_service = get_search_service()
        results = srch_service.search(message, language=language, top_k=top_k)

        # Debug logging for Authenticated route
        current_app.logger.info(f"Query: {message}")
        current_app.logger.info(f"Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            doc = result.get("document", {})
            current_app.logger.info(
                f"Result {i}: Article {doc.get('article', '?')} "
                f"(similarity: {result.get('similarity', 0):.3f}) - "
                f"Content preview: {doc.get('content', '')[:100]}"
            )

        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # 6. Stream Response & Save to DB
        # stream_assistant_reply handles saving the assistant's response to the DB
        return Response(
            stream_with_context(
                stream_assistant_reply(
                    message, 
                    vectors_json_str, 
                    conversation_id, 
                    language=language
                )
            ),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Language": language
            }
        )

    except Exception as e:
        logger.exception("chat_stream error")
        return jsonify({"error": f"Server error: {str(e)}"}), 500