"""
Global singleton instance of BilingualLLMService.

This module initializes the LLM service once when the server starts,
preventing model reloading on every request.
"""

import logging
from .bilingual_llm_service import BilingualLLMService

logger = logging.getLogger(__name__)

# Global singleton instance - loaded once on server startup
global_llm_service = None


def get_llm_service():
    """
    Get the global singleton LLM service instance.
    Initializes on first call, then returns the same instance.
    """
    global global_llm_service
    if global_llm_service is None:
        logger.info("Initializing global BilingualLLMService singleton...")
        global_llm_service = BilingualLLMService()
        logger.info("BilingualLLMService singleton initialized successfully")
    return global_llm_service
