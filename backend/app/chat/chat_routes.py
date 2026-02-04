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
from ..services.query_design_service.legal_qa_service import LegalQAService
from ..services.llm_service.instance import get_llm_service

logger = logging.getLogger(__name__)

# Global service instances (lazy loaded)
_language_service = None
_search_service = None
_qa_service = None


def get_language_service():
    """Get or create language service singleton"""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service


def get_search_service():
    """Get or create search service singleton"""
    global _search_service
    if _search_service is None:
        _search_service = BilingualSearchService()
    return _search_service


def get_qa_service():
    """Get or create QA service singleton"""
    global _qa_service
    if _qa_service is None:
        _qa_service = LegalQAService(config_path=None)
        # Assign the singleton LLM model to the service
        _qa_service.model = get_llm_service()
    return _qa_service

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








@chat_bp.route("/chat_stream", methods=["GET", "POST"])
@jwt_required
def chat_stream():
    try:
        user = getattr(g, "current_user", None)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        user_id = user["id"]

        # 1. Parse Input
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            message = str(data.get("message", ""))
            conversation_id = data.get("conversation_id")
            language = data.get("language", 'auto')
        else:
            message = request.args.get("message", "")
            conversation_id = request.args.get("conversation_id")
            language = request.args.get("language", 'auto')
            
        if not message:
            return jsonify({"error": "Missing message"}), 400

        # --- SECURITY LAYER (NEW) ---
        qa_service = get_qa_service()
        
        # Quick security check
        security_check = qa_service.security_filter.check_query_security(message)
        
        # Log the query
        event_id = qa_service.security_auditor.log_query(
            user_id, 
            message, 
            "secure" if security_check["is_secure"] else "rejected"
        )

        # Handle security violations
        if not security_check["is_secure"]:
            qa_service.security_auditor.log_response(user_id, event_id, "rejected")
            
            error_msg = (
                f"Requête non autorisée: {security_check.get('reason')}"
                if language == 'fr'
                else f"طلب غير مصرح به: {security_check.get('reason')}"
            )
            
            return jsonify({
                "error": "Security violation", 
                "message": error_msg,
                "event_id": event_id
            }), 403

        # Fetch conversation history for enhancement
        history = []
        if conversation_id:
            try:
                history = chat_models.get_messages(
                    conversation_id, 
                    limit=qa_service.config.max_history_items
                )
            except Exception as e:
                logger.warning(f"Could not fetch history: {e}")
        
        # Process query (enhancement + continuation detection)
        processed_result = qa_service.preprocess_query(
            message, 
            conversation_history=history, 
            user_id=user_id
        )
        
        # Handle rate limiting
        if processed_result.get("rate_limited"):
            qa_service.security_auditor.log_response(user_id, event_id, "rate_limited")
            
            error_msg = (
                "Limite de requêtes dépassée. Réessayez dans quelques instants."
                if processed_result["language"] == 'fr'
                else "تجاوز الحد المسموح. يرجى المحاولة بعد قليل."
            )
            
            return jsonify({
                "error": "Rate limit exceeded",
                "message": error_msg,
                "event_id": event_id
            }), 429

        # Handle LLM security violations
        if not processed_result["is_secure"]:
            qa_service.security_auditor.log_response(user_id, event_id, "rejected")
            
            error_msg = (
                f"Requête non autorisée: {processed_result.get('security_reason', '')}"
                if processed_result["language"] == 'fr'
                else f"طلب غير مصرح به: {processed_result.get('security_reason', '')}"
            )
            
            return jsonify({
                "error": "Security violation",
                "message": error_msg,
                "event_id": event_id
            }), 403

        # Extract enhanced query
        optimized_query = processed_result["processed_query"]
        detected_language = processed_result["language"]
        
        # --- END SECURITY LAYER ---

        # 2. Language Detection (use detected language from QA service)
        lang_service = get_language_service()
        if language == 'auto':
            language = detected_language  # Use QA service detection
        else:
            language = lang_service.normalize_language(language)
        
        # 3. Manage Conversation
        if conversation_id:
            conv = chat_models.get_conversation_for_user(int(conversation_id), user_id)
            if not conv: 
                return jsonify({"error": "Not found"}), 404
        else:
            title = message[:60]
            conversation_id = chat_models.create_conversation(user_id, title=title)

        # 4. Store User Message (store ORIGINAL message)
        chat_models.insert_message(
            conversation_id, 
            role="user", 
            content=message,  # Original user message
            sender_user_id=user_id
        )

        # 5. Search Documents (use OPTIMIZED query for better retrieval)
        srch_service = get_search_service()
        results = srch_service.hybrid_search(
            optimized_query,  # Use enhanced query
            language=language, 
            top_k=3
        )

        # Enhanced Logging
        current_app.logger.info(
            f"Event: {event_id} | Lang: {language} | "
            f"Original: {message[:40]}... | Enhanced: {optimized_query[:40]}..."
        )
        
        for i, res in enumerate(results, 1):
            art_id = res.get('article') or res.get('source', '?')
            content_snippet = res.get('content', '')[:100]
            sim = res.get('similarity', 0)
            current_app.logger.info(
                f"Result {i}: [{art_id}] (Sim: {sim:.3f}) - {content_snippet}"
            )

        vectors_json_str = json.dumps(results, ensure_ascii=False)

        # 6. Stream Response (use your existing implementation)
        return Response(
            stream_with_context(
                stream_assistant_reply(
                    optimized_query,  # Pass enhanced query to generation
                    vectors_json_str, 
                    conversation_id, 
                    language=language
                )
            ),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Language": language,
                "X-Event-ID": event_id,
                "X-Query-Enhanced": "true" if optimized_query != message else "false"
            }
        )

    except Exception as e:
        logger.exception("chat_stream error")
        
        # Log error in audit if available
        if 'event_id' in locals() and 'qa_service' in locals():
            try:
                qa_service.security_auditor.log_response(
                    user_id if 'user_id' in locals() else "unknown",
                    event_id,
                    "error"
                )
            except:
                pass
        
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# Optional: Statistics endpoint
@chat_bp.route("/query_stats", methods=["GET"])
@jwt_required
def query_stats():
    """Get query statistics for the current user"""
    try:
        user = getattr(g, "current_user", None)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        
        user_id = user["id"]
        qa_service = get_qa_service()
        
        # Get user statistics
        stats = qa_service.security_auditor.get_user_statistics(user_id)
        
        # Get remaining rate limit
        remaining = qa_service.rate_limiter.get_remaining_requests(user_id)
        stats["rate_limit_remaining"] = remaining
        stats["rate_limit_max"] = qa_service.config.rate_limit_max_requests
        
        return jsonify(stats), 200

    except Exception as e:
        logger.exception("query_stats error")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
