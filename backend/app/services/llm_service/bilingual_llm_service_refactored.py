import logging
import torch
import httpx
import threading
import re
from typing import Generator, Optional
from openai import OpenAI
from transformers import BitsAndBytesConfig, TextIteratorStreamer

logger = logging.getLogger(__name__)


class BilingualLLMService:
    """
    Bilingual LLM service supporting both local and API-based inference.
    
    Refactored to prevent Chinese character hallucination through:
    1. Strict generation parameters 
    2. Robust post-processing
    3. Proper stop criteria
    """
    
    def __init__(self):
        from app.config.settings import settings
        import os
        
        self.settings = settings
        self.use_local_llms = settings.USE_LOCAL_LLMS
        # Determine compute device
        self.device = os.getenv('COMPUTE_DEVICE', 'cuda').lower()
        if self.device not in ['cuda', 'cpu']:
            self.device = 'cuda'
        # Disable CUDA if CPU-only mode
        if self.device == 'cpu':
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
        
        # Lazy-loaded models
        self.french_llm = None
        self.french_tokenizer = None
        self.arabic_llm = None
        self.arabic_tokenizer = None
        
        # API client for fallback
        self.api_client = None
        if settings.OPENROUTER_API_KEY:
            try:
                import os
                # Disable proxies to avoid compatibility issues
                os.environ.pop('https_proxy', None)
                os.environ.pop('http_proxy', None)
                os.environ.pop('HTTPS_PROXY', None)
                os.environ.pop('HTTP_PROXY', None)
                
                # Create httpx client explicitly without proxies
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
                logger.error(f"Failed to initialize OpenRouter API client: {e}", exc_info=True)
                self.api_client = None
    
    def generate_completion(
        self,
        prompt: str,
        language: str = 'fr',
        stream: bool = False
    ) -> Generator[str, None, None]:
        """
        Generate completion with streaming support.
        
        Args:
            prompt: Input prompt
            language: 'fr' or 'ar'
            stream: Whether to stream results
            
        Yields:
            Response chunks as strings
        """
        language = self._normalize_language(language)
        
        try:
            if self.use_local_llms:
                if language == 'ar':
                    yield from self._generate_arabic_local(prompt, stream)
                else:
                    yield from self._generate_french_local(prompt, stream)
            else:
                yield from self._generate_api(prompt, language, stream)
        except Exception as e:
            logger.error(f"Error generating completion: {e}", exc_info=True)
            yield f"Error generating response: {str(e)}"
    
    def _normalize_language(self, language: str) -> str:
        """Normalize language code."""
        language = language.lower().strip()
        return 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'
    
    def _clean_llm_response(self, response: str, language: str = 'fr') -> str:
        """
        Robust post-processing to handle hallucination and ensure proper citation parsing.
        
        Instead of just counting characters, this implements sophisticated logic:
        - Discards responses with >20% non-target language characters
        - Preserves citations like [Article 50] correctly
        - Returns fallback message for invalid responses
        """
        if not response or not response.strip():
            return "Unable to generate a valid response from context."
        
        response = response.strip()
        
        # Count different types of characters
        total_chars = len([c for c in response if c.isalpha()])
        if total_chars == 0:
            return "Unable to generate a valid response from context."
        
        if language == 'ar':
            # Count Arabic characters
            target_chars = len(re.findall(r'[\u0600-\u06FF]', response))
            # Count non-Arabic alphabetic characters (excluding citations and punctuation)
            non_target_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff\u3040-\u309f]', response))
        else:
            # Count French/Latin characters
            target_chars = len(re.findall(r'[a-zA-ZàâäôöéèêëçùûüîïñÀÂÄÔÖÉÈÊËÇÙÛÜÎÏÑ]', response))
            # Count non-Latin alphabetic characters (Chinese, Arabic, etc.)
            non_target_chars = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u0600-\u06FF]', response))
        
        # Check if >20% non-target language
        non_target_ratio = non_target_chars / total_chars if total_chars > 0 else 0
        
        if non_target_ratio > 0.20:
            logger.warning(f"[{language}] Response contains {non_target_ratio:.1%} non-target language characters. Discarding.")
            return "Unable to generate a valid response from context."
        
        # Extract and preserve sections with citations
        answer_text = ""
        sources_text = ""
        
        # Parse response format based on language
        if language == 'ar':
            # Look for [الإجابة] section
            if "[الإجابة]" in response:
                parts = response.split("[الإجابة]")
                if len(parts) > 1:
                    answer_part = parts[-1]
                    if "[المصادر]" in answer_part:
                        answer_text = answer_part.split("[المصادر]")[0].strip()
                        sources_text = answer_part.split("[المصادر]")[-1].strip()
                    else:
                        answer_text = answer_part.strip()
            else:
                # Fallback: take full response but clean format markers
                answer_text = response.replace("[الإجابة]", "").replace("[المصادر]", "").strip()
        else:
            # Look for [RÉPONSE] section  
            if "[RÉPONSE]" in response:
                parts = response.split("[RÉPONSE]")
                if len(parts) > 1:
                    answer_part = parts[-1]
                    if "[SOURCES]" in answer_part:
                        answer_text = answer_part.split("[SOURCES]")[0].strip()
                        sources_text = answer_part.split("[SOURCES]")[-1].strip()
                    else:
                        answer_text = answer_part.strip()
            else:
                # Fallback: take full response but clean format markers
                answer_text = response.replace("[RÉPONSE]", "").replace("[SOURCES]", "").strip()
        
        # Preserve citations correctly - don't cut them off
        # Citations like [Article 50], [المادة 15] should be preserved
        citation_pattern = r'\[[^\]]{1,50}\]'  # Match [content] with reasonable length limit
        citations = re.findall(citation_pattern, answer_text)
        
        # Clean and limit answer length while preserving citations
        sentences = []
        if language == 'ar':
            # Split on Arabic sentence endings, preserve citations
            parts = re.split(r'[.!?؟]', answer_text)
        else:
            # Split on French sentence endings, preserve citations  
            parts = re.split(r'[.!?]', answer_text)
        
        # Take first 3 meaningful sentences
        sentence_count = 0
        for part in parts:
            if part.strip() and sentence_count < 3:
                sentences.append(part.strip())
                sentence_count += 1
        
        # Reconstruct answer with proper punctuation
        if sentences:
            answer_text = '. '.join(sentences)
            if not answer_text.endswith(('.', '!', '?', '؟')):
                answer_text += '.'
        
        # Clean up sources section
        if sources_text:
            source_lines = [line.strip() for line in sources_text.split('\n') if line.strip()]
            # Remove duplicates while preserving order
            seen = set()
            unique_sources = []
            for line in source_lines:
                # Normalize for duplicate detection
                normalized = re.sub(r'^\d+\.\s*', '', line.strip())
                if normalized and normalized not in seen:
                    unique_sources.append(line)
                    seen.add(normalized)
            sources_text = '\n'.join(unique_sources[:5])  # Max 5 sources
        
        # Combine final response
        if sources_text:
            if language == 'ar':
                return f"{answer_text}\n\n[المصادر]\n{sources_text}"
            else:
                return f"{answer_text}\n\n[SOURCES]\n{sources_text}"
        else:
            return answer_text if answer_text else "Unable to generate a valid response from context."
    
    def _load_french_llm(self):
        """Load French LLM (Vigogne-2-7B) with lazy loading."""
        if self.french_llm is not None:
            return
        
        logger.info(f"Loading French LLM: {self.settings.FRENCH_LLM_MODEL}")
        logger.info(f"Device: {self.device}, Use quantization: {self.settings.USE_4BIT_QUANTIZATION}")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            self.french_tokenizer = AutoTokenizer.from_pretrained(
                self.settings.FRENCH_LLM_MODEL,
                local_files_only=True
            )
            
            if self.settings.USE_4BIT_QUANTIZATION and self.device == 'cuda':
                # 4-bit quantization is ONLY for CUDA
                try:
                    logger.info("CUDA device configured. Loading French LLM with 4-bit quantization...")
                    quant_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    self.french_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.FRENCH_LLM_MODEL,
                        quantization_config=quant_config,
                        device_map="auto",
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("✓ French LLM loaded with 4-bit quantization (CUDA)")
                except Exception as quant_error:
                    logger.warning(f"4-bit quantization failed for French LLM: {quant_error}. Falling back to float16 loading.")
                    # Fallback: explicit float16 loading without quantization
                    self.french_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.FRENCH_LLM_MODEL,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("French LLM loaded with float16 (fallback from quantization)")
            else:
                # CPU or quantization disabled: use bfloat16 (CPU-compatible) with fallback to float32
                logger.info("Loading French LLM on CPU with bfloat16...")
                try:
                    dtype = torch.bfloat16
                    self.french_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.FRENCH_LLM_MODEL,
                        torch_dtype=dtype,
                        device_map=None,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("✓ French LLM loaded with bfloat16 (CPU-compatible)")
                except Exception as bfloat_error:
                    logger.warning(f"bfloat16 loading failed: {bfloat_error}. Falling back to float32...")
                    self.french_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.FRENCH_LLM_MODEL,
                        torch_dtype=torch.float32,
                        device_map=None,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("✓ French LLM loaded with float32 (fallback)")
            
            logger.info("French LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load French LLM: {e}", exc_info=True)
            self.french_llm = None
    
    def _load_arabic_llm(self):
        """Load Arabic LLM (Qwen2.5-7B) with lazy loading."""
        if self.arabic_llm is not None:
            return
        
        logger.info(f"Loading Arabic LLM: {self.settings.ARABIC_LLM_MODEL}")
        logger.info(f"Device: {self.device}, Use quantization: {self.settings.USE_4BIT_QUANTIZATION}")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            self.arabic_tokenizer = AutoTokenizer.from_pretrained(
                self.settings.ARABIC_LLM_MODEL,
                local_files_only=True
            )
            
            if self.settings.USE_4BIT_QUANTIZATION and self.device == 'cuda':
                # 4-bit quantization is ONLY for CUDA
                try:
                    logger.info("CUDA device configured. Loading Arabic LLM with 4-bit quantization...")
                    quant_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    self.arabic_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.ARABIC_LLM_MODEL,
                        quantization_config=quant_config,
                        device_map="auto",
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("✓ Arabic LLM loaded with 4-bit quantization (CUDA)")
                except Exception as quant_error:
                    logger.warning(f"4-bit quantization failed for Arabic LLM: {quant_error}. Falling back to float16 loading.")
                    # Fallback: explicit float16 loading without quantization
                    self.arabic_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.ARABIC_LLM_MODEL,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("Arabic LLM loaded with float16 (fallback from quantization)")
            else:
                # CPU or quantization disabled: use bfloat16 (CPU-compatible) with fallback to float32
                logger.info("Loading Arabic LLM on CPU with bfloat16...")
                try:
                    dtype = torch.bfloat16
                    self.arabic_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.ARABIC_LLM_MODEL,
                        torch_dtype=dtype,
                        device_map=None,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("✓ Arabic LLM loaded with bfloat16 (CPU-compatible)")
                except Exception as bfloat_error:
                    logger.warning(f"bfloat16 loading failed: {bfloat_error}. Falling back to float32...")
                    self.arabic_llm = AutoModelForCausalLM.from_pretrained(
                        self.settings.ARABIC_LLM_MODEL,
                        torch_dtype=torch.float32,
                        device_map=None,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                    logger.info("✓ Arabic LLM loaded with float32 (fallback)")
            
            logger.info("Arabic LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load Arabic LLM: {e}", exc_info=True)
            self.arabic_llm = None
    
    def _generate_french_local(self, prompt: str, stream: bool = False) -> Generator[str, None, None]:
        """
        Generate French response using local Vigogne model.
        
        REFACTORED with strict factual mode:
        - temperature=0.1 (strict factual mode)
        - repetition_penalty=1.1 (balanced grammar preservation)
        - stop_strings for proper termination
        """
        self._load_french_llm()
        
        if self.french_llm is None:
            logger.warning("French LLM not available, falling back to API")
            yield from self._generate_api(prompt, 'fr', stream)
            return
        
        try:
            inputs = self.french_tokenizer(prompt, return_tensors="pt")
            if self.device == 'cuda' and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Define stop strings for proper termination
            stop_strings = ["</s>", "[END]", "---", "\n\nQuestion:", "\n\nQUESTION:"]
            
            if stream:
                # Use TextIteratorStreamer for real-time token streaming
                streamer = TextIteratorStreamer(
                    self.french_tokenizer,
                    skip_special_tokens=True,
                    skip_prompt=True
                )
                
                # Run generation in a separate thread with STRICT PARAMETERS
                generation_thread = threading.Thread(
                    target=self.french_llm.generate,
                    kwargs={
                        **inputs,
                        "max_new_tokens": 200,
                        "temperature": 0.1,        # STRICT factual mode
                        "top_p": 0.9,
                        "do_sample": True,
                        "pad_token_id": self.french_tokenizer.eos_token_id,
                        "eos_token_id": self.french_tokenizer.eos_token_id,
                        "repetition_penalty": 1.1,  # Balanced grammar preservation
                        "no_repeat_ngram_size": 3,
                        "streamer": streamer
                    }
                )
                generation_thread.start()
                
                # Collect response for post-processing
                collected_response = ""
                for token in streamer:
                    if token:
                        # Check for stop strings
                        if any(stop_str in token for stop_str in stop_strings):
                            break
                        collected_response += token
                        yield token
                
                generation_thread.join()
                logger.info("French generation completed")
            else:
                # Non-streaming mode with STRICT PARAMETERS
                with torch.no_grad():
                    outputs = self.french_llm.generate(
                        **inputs,
                        max_new_tokens=200,
                        temperature=0.1,        # STRICT factual mode
                        top_p=0.9,
                        do_sample=True,
                        pad_token_id=self.french_tokenizer.eos_token_id,
                        eos_token_id=self.french_tokenizer.eos_token_id,
                        repetition_penalty=1.1,  # Balanced grammar preservation
                        no_repeat_ngram_size=3
                    )
                
                response = self.french_tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Clean response
                if "<|assistant|>:" in response:
                    response = response.split("<|assistant|>:")[-1].strip()
                else:
                    response = response[len(prompt):].strip()
                
                # Apply robust post-processing
                response = self._clean_llm_response(response, language='fr')
                
                yield response
                
        except Exception as e:
            logger.error(f"Error generating French response: {e}", exc_info=True)
            yield f"Error generating French response: {str(e)}"
    
    def _generate_arabic_local(self, prompt: str, stream: bool = False) -> Generator[str, None, None]:
        """
        Generate Arabic response using local Qwen model.
        
        REFACTORED with strict factual mode:
        - temperature=0.1 (strict factual mode)
        - repetition_penalty=1.1 (balanced grammar preservation)
        - stop_strings for proper termination
        """
        self._load_arabic_llm()
        
        if self.arabic_llm is None:
            logger.warning("Arabic LLM not available, falling back to API")
            yield from self._generate_api(prompt, 'ar', stream)
            return
        
        try:
            inputs = self.arabic_tokenizer(prompt, return_tensors="pt")
            if self.device == 'cuda' and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Define stop strings for proper termination
            stop_strings = ["</s>", "[END]", "---", "\n\nسؤال:", "\n\nالسؤال:"]
            
            if stream:
                # Use TextIteratorStreamer for real-time token streaming
                streamer = TextIteratorStreamer(
                    self.arabic_tokenizer,
                    skip_special_tokens=True,
                    skip_prompt=True
                )
                
                # Run generation in a separate thread with STRICT PARAMETERS
                generation_thread = threading.Thread(
                    target=self.arabic_llm.generate,
                    kwargs={
                        **inputs,
                        "max_new_tokens": 200,
                        "temperature": 0.1,        # STRICT factual mode
                        "top_p": 0.9,
                        "do_sample": True,
                        "pad_token_id": self.arabic_tokenizer.eos_token_id,
                        "eos_token_id": self.arabic_tokenizer.eos_token_id,
                        "repetition_penalty": 1.1,  # Balanced grammar preservation
                        "no_repeat_ngram_size": 3,
                        "streamer": streamer
                    }
                )
                generation_thread.start()
                
                # Collect response for post-processing
                collected_response = ""
                for token in streamer:
                    if token:
                        # Check for stop strings
                        if any(stop_str in token for stop_str in stop_strings):
                            break
                        collected_response += token
                        yield token
                
                generation_thread.join()
                logger.info("Arabic generation completed")
            else:
                # Non-streaming mode with STRICT PARAMETERS
                with torch.no_grad():
                    outputs = self.arabic_llm.generate(
                        **inputs,
                        max_new_tokens=200,
                        temperature=0.1,        # STRICT factual mode
                        top_p=0.9,
                        do_sample=True,
                        pad_token_id=self.arabic_tokenizer.eos_token_id,
                        eos_token_id=self.arabic_tokenizer.eos_token_id,
                        repetition_penalty=1.1,  # Balanced grammar preservation
                        no_repeat_ngram_size=3
                    )
                
                response = self.arabic_tokenizer.decode(outputs[0], skip_special_tokens=True)
                response = response.split("Answer (in Arabic, comprehensive):")[-1].strip() if "Answer (in Arabic, comprehensive):" in response else response[len(prompt):].strip()
                
                # Apply robust post-processing
                response = self._clean_llm_response(response, language='ar')
                
                yield response
                
        except Exception as e:
            logger.error(f"Error generating Arabic response: {e}", exc_info=True)
            yield f"Error generating Arabic response: {str(e)}"
    
    def _generate_api(
        self,
        prompt: str,
        language: str = 'fr',
        stream: bool = False
    ) -> Generator[str, None, None]:
        """Generate response using OpenRouter API with same strict parameters."""
        if not self.api_client:
            logger.warning("API client not configured. Please set OPENROUTER_API_KEY.")
            yield "API client not configured"
            return
        
        try:
            # Use same strict parameters as local models
            response = self.api_client.chat.completions.create(
                model=self.settings.DEFAULT_LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                temperature=0.1,    # STRICT factual mode
                max_tokens=200
            )
            
            if stream:
                collected_response = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        collected_response += token
                        yield token
                        
                # Apply post-processing to collected response
                if collected_response:
                    cleaned = self._clean_llm_response(collected_response, language)
                    if cleaned != collected_response:
                        yield f"\n[Processed: {cleaned}]"
            else:
                if hasattr(response.choices[0].message, 'content'):
                    api_response = response.choices[0].message.content
                    # Apply robust post-processing
                    cleaned_response = self._clean_llm_response(api_response, language)
                    yield cleaned_response
                else:
                    yield "No response from API"
                
        except Exception as e:
            logger.error(f"Error calling API LLM: {e}", exc_info=True)
            yield f"Error: {str(e)}"