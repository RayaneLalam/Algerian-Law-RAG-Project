import logging
import httpx
import threading
import re
from typing import Generator, Optional
from openai import OpenAI
from app.config.settings import settings

logger = logging.getLogger(__name__)

class BilingualLLMService:
    """
    Bilingual LLM service using Ollama (deepseek-r1:8b) for local inference 
    and OpenRouter as fallback. 
    
    Preserves original logic for:
    1. Strict generation parameters 
    2. Robust post-processing (Citation preservation & Language checks)
    """
    
    def __init__(self):
        self.settings = settings
        self.use_local_llms = settings.USE_LOCAL_LLMS
        self.local_model = "deepseek-r1:8b"
        
        # Initialize Ollama Client (OpenAI compatible)
        try:
            self.ollama_client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None

        # API client for fallback
        self.api_client = None
        if settings.OPENROUTER_API_KEY:
            try:
                import os
                os.environ.pop('https_proxy', None)
                os.environ.pop('http_proxy', None)
                
                http_client = httpx.Client(
                    timeout=120.0,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                )
                
                self.api_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.OPENROUTER_API_KEY,
                    http_client=http_client
                )
                logger.info("OpenRouter API client initialized for LLM fallback")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter API client: {e}")

    def generate_completion(
        self,
        prompt: str,
        language: str = 'fr',
        stream: bool = False
    ) -> Generator[str, None, None]:
        """
        Matches original signature to prevent 'missing positional argument' errors.
        """
        language = self._normalize_language(language)
        
        try:
            if self.use_local_llms and self.ollama_client:
                # We use the same local handler logic but directed to Ollama
                if language == 'ar':
                    yield from self._generate_local_ollama(prompt, 'ar', stream)
                else:
                    yield from self._generate_local_ollama(prompt, 'fr', stream)
            else:
                yield from self._generate_api(prompt, language, stream)
        except Exception as e:
            logger.error(f"Error generating completion: {e}", exc_info=True)
            yield f"Error generating response: {str(e)}"

    def _generate_local_ollama(self, prompt: str, language: str, stream: bool) -> Generator[str, None, None]:
        """Replacement for _generate_french_local and _generate_arabic_local using Ollama."""
        try:
            response = self.ollama_client.chat.completions.create(
                model=self.local_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Matches original strict factual mode
                stream=stream,
                max_tokens=800
            )

            if stream:
                collected_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        collected_response += token
                        yield token
                # Final log for internal tracking
                logger.info(f"Local {language} generation (Ollama) completed")
            else:
                raw_text = response.choices[0].message.content
                logger.debug(f"Raw LLM [{language}] output: {raw_text!r}")
                yield self._clean_llm_response(raw_text, language=language)

                
        except Exception as e:
            logger.warning(f"Local Ollama failed: {e}. Falling back to API.")
            yield from self._generate_api(prompt, language, stream)

    def _clean_llm_response(self, response: str, language: str = 'fr') -> str:
        """
        EXACT SAME LOGIC from your original code.
        Handles citations, language ratios, and formatting markers.
        """
        if not response or not response.strip():
            return "Unable to generate a valid response from context."
        
        response = response.strip()
        total_chars = len([c for c in response if c.isalpha()])
        if total_chars == 0:
            return "Unable to generate a valid response from context."
        
        # Language detection logic
        if language == 'ar':
            target_chars = len(re.findall(r'[\u0600-\u06FF]', response))
            non_target_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff\u3040-\u309f]', response))
        else:
            target_chars = len(re.findall(r'[a-zA-ZàâäôöéèêëçùûüîïñÀÂÄÔÖÉÈÊËÇÙÛÜÎÏÑ]', response))
            non_target_chars = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u0600-\u06FF]', response))
        
        non_target_ratio = non_target_chars / total_chars if total_chars > 0 else 0
        if non_target_ratio > 0.20:
            logger.warning(f"[{language}] High non-target ratio ({non_target_ratio:.1%}). Discarding.")
            return "Unable to generate a valid response from context."
        
        # Citation and Section parsing (RÉPONSE / الإجابة)
        answer_text = ""
        sources_text = ""
        
        if language == 'ar':
            if "[الإجابة]" in response:
                parts = response.split("[الإجابة]")
                answer_part = parts[-1]
                if "[المصادر]" in answer_part:
                    answer_text = answer_part.split("[المصادر]")[0].strip()
                    sources_text = answer_part.split("[المصادر]")[-1].strip()
                else:
                    answer_text = answer_part.strip()
            else:
                answer_text = response.replace("[الإجابة]", "").replace("[المصادر]", "").strip()
        else:
            if "[RÉPONSE]" in response:
                parts = response.split("[RÉPONSE]")
                answer_part = parts[-1]
                if "[SOURCES]" in answer_part:
                    answer_text = answer_part.split("[SOURCES]")[0].strip()
                    sources_text = answer_part.split("[SOURCES]")[-1].strip()
                else:
                    answer_text = answer_part.strip()
            else:
                answer_text = response.replace("[RÉPONSE]", "").replace("[SOURCES]", "").strip()

        # Sentence limiting logic (First 3 sentences)
        sep = r'[.!?؟]' if language == 'ar' else r'[.!?]'
        parts = re.split(sep, answer_text)
        sentences = [p.strip() for p in parts if p.strip()][:3]
        
        if sentences:
            answer_text = '. '.join(sentences)
            if not answer_text.endswith(('.', '!', '?', '؟')):
                answer_text += '.'

        # Source reconstruction
        if sources_text:
            source_lines = list(dict.fromkeys([line.strip() for line in sources_text.split('\n') if line.strip()]))
            sources_text = '\n'.join(source_lines[:5])
            header = "[المصادر]" if language == 'ar' else "[SOURCES]"
            return f"{answer_text}\n\n{header}\n{sources_text}"
        
        return answer_text if answer_text else "Unable to generate a valid response from context."

    def _generate_api(self, prompt: str, language: str = 'fr', stream: bool = False) -> Generator[str, None, None]:
        """Generate response using OpenRouter API."""
        if not self.api_client:
            yield "API client not configured"
            return
        
        try:
            response = self.api_client.chat.completions.create(
                model=self.settings.DEFAULT_LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                temperature=0.1,
                max_tokens=800
            )
            
            if stream:
                collected = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        collected += token
                        yield token
            else:
                yield self._clean_llm_response(response.choices[0].message.content, language)
        except Exception as e:
            logger.error(f"API Error: {e}")
            yield f"Error: {str(e)}"

    def _normalize_language(self, language: str) -> str:
        language = language.lower().strip()
        return 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'