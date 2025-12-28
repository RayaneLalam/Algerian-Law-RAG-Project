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
        messages = chat_models.get_conversation_messages(
            conversation_id, user_id)

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
            model_version_id = chat_models.get_default_model_version()
            if not model_version_id:
                return jsonify({"error": "No model versions available"}), 500

        # validate or create conversation
        if conversation_id:
            # Convert to int if it's a string
            try:
                conversation_id = int(conversation_id)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid conversation_id format"}), 400

            conv = chat_models.get_conversation_for_user(
                conversation_id, user_id)
            if not conv:
                return jsonify({"error": "Conversation not found or access denied"}), 404
        else:
            title = (message[:60] + "...") if len(message) > 60 else message
            conversation_id = chat_models.create_conversation(
                user_id, title=title)

        # Update conversation timestamp
        chat_models.update_conversation_timestamp(conversation_id)

        # store user message with model_version_id
        chat_models.insert_message(
            conversation_id,
            role="user",
            content=message,
            sender_user_id=user_id,
        )

        # Search for relevant articles
        top_k = 3  # Increased to get more context
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
