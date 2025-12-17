from flask import current_app
from . import chat_models
from ..utils.prompt_utils import _load_prompt_template, _format_context_from_results
import json
from ..services.llm_service.llm_api import LLM_Service
import os

PROMPT_TEMPLATE_PATH = os.path.join(".", "app", "prompt_templates", "qa_with_context.txt")
llm_service = LLM_Service()


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




def stream_assistant_reply(message, vectors_json_str, conversation_id):
    """
    Generator that yields SSE chunks from make_reply_stream(...).
    On finish (or partial finish), saves the concatenated assistant message
    into the DB and updates conversation timestamp.
    """
    assistant_chunks = []
    try:
        for chunk in make_reply_stream(message, vectors_json_str):
            assistant_chunks.append(chunk)
            # Send chunk in SSE format without JSON wrapping
            yield f"data: {chunk}\n\n"
        
        # Signal completion
        yield "data: [DONE]\n\n"
        
    except GeneratorExit:
        # client disconnected — fall through to finally block to save partial response
        current_app.logger.debug("Client disconnected from SSE stream")
    except Exception as e:
        err = f"[server error while generating reply: {e}]"
        assistant_chunks.append(err)
        yield f"data: {err}\n\n"
    finally:
        # join and persist assistant full text (even if partial)
        assistant_full = "".join(assistant_chunks).strip()
        if assistant_full:
            try:
                chat_models.insert_message(conversation_id, "assistant", assistant_full)
                chat_models.update_conversation_timestamp(conversation_id)
            except Exception:
                current_app.logger.exception("Failed to save assistant message")


