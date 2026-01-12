from flask import current_app
from . import chat_models
from ..utils.prompt_utils import load_language_prompt_template, _format_context_from_results
from ..services.llm_service.instance import get_llm_service
import json
import logging

logger = logging.getLogger(__name__)


def make_reply_stream(received_message: str, vectors_json_str: str, language: str = 'fr'):
    """Generate streaming reply with language awareness using global LLM service."""
    
    try:
        results = json.loads(vectors_json_str) if vectors_json_str else []
    except Exception:
        results = []
    
    language = language.lower().strip()
    language = 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'
    
    context_block = _format_context_from_results(results, language=language)
    template = load_language_prompt_template(language)
    
    try:
        prompt = template.format(query=received_message, context=context_block)
    except Exception:
        prompt = f"Question: {received_message}\n\nContext:\n{context_block}"
    
    # Use global singleton instance - no new instance creation
    llm_service = get_llm_service()
    return llm_service.generate_completion(prompt, language=language, stream=True)


def stream_assistant_reply_demo(message, vectors_json_str, language: str = 'fr'):
    """
    Demo streaming (no auth) - doesn't save to database.
    Just yields SSE chunks without persisting.
    """
    try:
        for chunk in make_reply_stream(message, vectors_json_str, language=language):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
    except GeneratorExit:
        current_app.logger.debug("Client disconnected from SSE stream")
    except Exception as e:
        err = f"[server error while generating reply: {e}]"
        current_app.logger.exception("stream_assistant_reply_demo error")
        yield f"data: {json.dumps({'chunk': err})}\n\n"


def stream_assistant_reply(message, vectors_json_str, conversation_id, language: str = 'fr'):
    """
    Generator that yields SSE chunks from make_reply_stream(...).
    On finish (or partial finish), saves the concatenated assistant message
    into the DB and updates conversation timestamp.
    """
    assistant_chunks = []
    try:
        for chunk in make_reply_stream(message, vectors_json_str, language=language):
            assistant_chunks.append(chunk)
            # Send chunk in SSE format without JSON wrapping
            yield f"data: {chunk}\n\n"
        
        # Signal completion
        yield "data: [DONE]\n\n"
        
    except GeneratorExit:
        current_app.logger.debug("Client disconnected from SSE stream")
    except Exception as e:
        err = f"[server error while generating reply: {e}]"
        assistant_chunks.append(err)
        yield f"data: {err}\n\n"
    finally:
        # join and persist assistant full text (even if partial)
        print("got here")
        assistant_full = "".join(assistant_chunks).strip()
        if assistant_full and conversation_id:
            try:
                chat_models.insert_message(conversation_id, "assistant", content=assistant_full)
                chat_models.update_conversation_timestamp(conversation_id)
            except Exception:
                current_app.logger.exception("Failed to save assistant message")


