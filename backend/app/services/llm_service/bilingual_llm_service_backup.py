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
    
    def _create_bad_words_filter(self, tokenizer, language='ar'):
        """
        Create a list of token IDs for Chinese/Japanese characters to block during generation.
        """
        import re
        bad_words_ids = []
        
        try:
            # Get vocabulary from tokenizer
            vocab = tokenizer.get_vocab()
            
            # Find tokens that contain Chinese/Japanese characters
            for token, token_id in vocab.items():
                # Check if token contains Chinese/Japanese characters
                if re.search(r'[\u4e00-\u9fff\u3040-\u309f]', str(token)):
                    bad_words_ids.append([token_id])  # Each bad word should be a list
                    
            logger.info(f"[{language}] Blocking {len(bad_words_ids)} Chinese/Japanese tokens")
            return bad_words_ids if bad_words_ids else None
            
        except Exception as e:
            logger.warning(f"[{language}] Could not create bad words filter: {e}")
            return None
    
    def _clean_llm_response(self, response: str, language: str = 'fr') -> str:
        """
        Clean LLM response by extracting answer and sources sections.
        Removes template text that shouldn't be in the output.
        Handles hallucination in other languages.
        """
        import re
        
        # Check for hallucination in Chinese/Japanese - STRICTER THRESHOLD
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f]', response))
        if chinese_chars > 2:  # ANY Chinese characters beyond 2 = immediate warning
            logger.warning(f"[{language}] Detected hallucination: {chinese_chars} Chinese/Japanese characters")
            return "Warning: Model generated response in unsupported language."
        
        # Extract sections
        answer_text = ""
        sources_text = ""
        
        # Try to extract [الإجابة] or [RÉPONSE] section
        if "[الإجابة]" in response:
            parts = response.split("[الإجابة]")
            if len(parts) > 1:
                answer_part = parts[-1]
                if "[المصادر]" in answer_part:
                    answer_text = answer_part.split("[المصادر]")[0].strip()
                    sources_text = answer_part.split("[المصادر]")[-1].strip()
                else:
                    answer_text = answer_part.strip()
        elif "[RÉPONSE]" in response:
            parts = response.split("[RÉPONSE]")
            if len(parts) > 1:
                answer_part = parts[-1]
                if "[SOURCES]" in answer_part:
                    answer_text = answer_part.split("[SOURCES]")[0].strip()
                    sources_text = answer_part.split("[SOURCES]")[-1].strip()
                else:
                    answer_text = answer_part.strip()
        else:
            # Fallback: just clean template markers
            answer_text = response.replace("[الإجابة]", "").replace("[المصادر]", "").replace("[RÉPONSE]", "").replace("[SOURCES]", "").strip()
        
        # Limit answer to 4 sentences max
        if language == 'ar':
            # Split on Arabic sentence endings
            sentences = [s.strip() for s in re.split(r'[.!?؟،]', answer_text) if s.strip()]
        else:
            # Split on French sentence endings
            sentences = [s.strip() for s in re.split(r'[.!?]', answer_text) if s.strip()]
        
        # Take only first 4 sentences
        answer_text = ". ".join(sentences[:4])
        if answer_text and not answer_text.endswith(('.', '!', '?', '؟')):
            answer_text += "."
        
        # Deduplicate sources - remove repetitions
        if sources_text:
            source_lines = [line.strip() for line in sources_text.split('\n') if line.strip()]
            # Remove duplicates while preserving order
            seen = set()
            unique_sources = []
            for line in source_lines:
                if line not in seen:
                    unique_sources.append(line)
                    seen.add(line)
            sources_text = "\n".join(unique_sources[:10])  # Max 10 sources
        
        # Combine cleaned response
        if sources_text:
            if language == 'ar':
                return f"{answer_text}\n\n[المصادر]\n{sources_text}"
            else:
                return f"{answer_text}\n\n[SOURCES]\n{sources_text}"
        else:
            return answer_text
    
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
        """Generate French response using local Vigogne model with real-time streaming."""
        self._load_french_llm()
        
        if self.french_llm is None:
            logger.warning("French LLM not available, falling back to API")
            yield from self._generate_api(prompt, 'fr', stream)
            return
        
        try:
            inputs = self.french_tokenizer(prompt, return_tensors="pt")
            if self.device == 'cuda' and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            if stream:
                # Use TextIteratorStreamer for real-time token streaming
                streamer = TextIteratorStreamer(
                    self.french_tokenizer,
                    skip_special_tokens=True,
                    skip_prompt=True
                )
                
                # Create bad words filter to block Chinese tokens
                bad_words_ids = self._create_bad_words_filter(self.french_tokenizer, 'fr')
                
                # Run generation in a separate thread with stricter parameters
                generation_kwargs = {
                    **inputs,
                    "max_new_tokens": 150,  # Stricter limit
                    "temperature": 0.1,     # Very low temperature
                    "top_p": 0.8,          # More restrictive
                    "do_sample": True,
                    "pad_token_id": self.french_tokenizer.eos_token_id,
                    "eos_token_id": self.french_tokenizer.eos_token_id,
                    "repetition_penalty": 2.0,  # Higher penalty
                    "no_repeat_ngram_size": 4,  # Stricter n-gram
                    "streamer": streamer
                }
                
                # Add bad words filter if available
                if bad_words_ids:
                    generation_kwargs["bad_words_ids"] = bad_words_ids
                
                generation_thread = threading.Thread(
                    target=self.french_llm.generate,
                    kwargs=generation_kwargs
                )
                generation_thread.start()
                
                # Collect streamed tokens and apply cleaning
                collected_response = ""
                chinese_detected = False
                token_count = 0
                
                for token in streamer:
                    if token:
                        token_count += 1
                        # Early detection of Chinese characters
                        import re
                        if not chinese_detected:
                            chinese_in_token = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f]', token))
                            if chinese_in_token > 0:
                                chinese_detected = True
                                logger.warning(f"[French] Early Chinese character detection in token {token_count}")
                                yield " Warning: Model generated response in unsupported language."
                                break
                        
                        collected_response += token
                        # Stop if response gets too long (safety check)
                        if len(collected_response) > 2000:  # Character limit
                            logger.warning(f"[French] Response too long, stopping generation")
                            break
                        
                        logger.debug(f"[French] Yielding token: {token[:50]}")
                        yield token
                
                generation_thread.join()
                
                # If no Chinese was detected during streaming, still clean the final response
                if not chinese_detected and collected_response:
                    cleaned_response = self._clean_llm_response(collected_response, language='fr')
                    # If cleaning detected issues, send a warning as the final token
                    if "Warning" in cleaned_response:
                        yield "\n[Cleaned] Response contained unsupported content."
                
                logger.info("French generation completed")
            else:
                # Non-streaming mode with stricter parameters
                with torch.no_grad():
                    # Create bad words filter
                    bad_words_ids = self._create_bad_words_filter(self.french_tokenizer, 'fr')
                    
                    generation_kwargs = {
                        **inputs,
                        "max_new_tokens": 150,     # Stricter limit
                        "temperature": 0.1,        # Very low temperature
                        "top_p": 0.8,             # More restrictive
                        "do_sample": True,
                        "pad_token_id": self.french_tokenizer.eos_token_id,
                        "eos_token_id": self.french_tokenizer.eos_token_id,
                        "repetition_penalty": 2.0,  # Higher penalty
                        "no_repeat_ngram_size": 4   # Stricter n-gram
                    }
                    
                    # Add bad words filter if available
                    if bad_words_ids:
                        generation_kwargs["bad_words_ids"] = bad_words_ids
                    
                    outputs = self.french_llm.generate(**generation_kwargs)
                
                response = self.french_tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                if "<|assistant|>:" in response:
                    response = response.split("<|assistant|>:")[-1].strip()
                else:
                    response = response[len(prompt):].strip()
                
                # Clean output: extract answer and sources
                response = self._clean_llm_response(response, language='fr')
                
                yield response
                
        except Exception as e:
            logger.error(f"Error generating French response: {e}", exc_info=True)
            yield f"Error generating French response: {str(e)}"
    
    def _generate_arabic_local(self, prompt: str, stream: bool = False) -> Generator[str, None, None]:
        """Generate Arabic response using local Qwen model with real-time streaming."""
        self._load_arabic_llm()
        
        if self.arabic_llm is None:
            logger.warning("Arabic LLM not available, falling back to API")
            yield from self._generate_api(prompt, 'ar', stream)
            return
        
        try:
            inputs = self.arabic_tokenizer(prompt, return_tensors="pt")
            if self.device == 'cuda' and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            if stream:
                # Use TextIteratorStreamer for real-time token streaming
                streamer = TextIteratorStreamer(
                    self.arabic_tokenizer,
                    skip_special_tokens=True,
                    skip_prompt=True
                )
                
                # Create bad words filter to block Chinese tokens
                bad_words_ids = self._create_bad_words_filter(self.arabic_tokenizer, 'ar')
                
                # Run generation in a separate thread with stricter parameters
                generation_kwargs = {
                    **inputs,
                    "max_new_tokens": 150,  # Even stricter limit
                    "temperature": 0.1,     # Very low temperature
                    "top_p": 0.8,          # More restrictive
                    "do_sample": True,
                    "pad_token_id": self.arabic_tokenizer.eos_token_id,
                    "eos_token_id": self.arabic_tokenizer.eos_token_id,
                    "repetition_penalty": 2.0,  # Higher penalty
                    "no_repeat_ngram_size": 4,  # Stricter n-gram
                    "streamer": streamer
                }
                
                # Add bad words filter if available
                if bad_words_ids:
                    generation_kwargs["bad_words_ids"] = bad_words_ids
                
                generation_thread = threading.Thread(
                    target=self.arabic_llm.generate,
                    kwargs=generation_kwargs
                )
                generation_thread.start()
                
                # Collect streamed tokens and clean final response
                collected_response = ""
                chinese_detected = False
                token_count = 0
                
                for token in streamer:
                    if token:
                        token_count += 1
                        # Early detection of Chinese characters
                        import re
                        if not chinese_detected:
                            chinese_in_token = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f]', token))
                            if chinese_in_token > 0:
                                chinese_detected = True
                                logger.warning(f"[Arabic] Early Chinese character detection in token {token_count}")
                                yield "⚠️ Warning: Model generated response in unsupported language."
                                break
                        
                        collected_response += token
                        # Stop if response gets too long (safety check)
                        if len(collected_response) > 2000:  # Character limit
                            logger.warning(f"[Arabic] Response too long, stopping generation")
                            break
                        
                        logger.debug(f"[Arabic] Yielding token: {token[:50]}")
                        yield token
                
                generation_thread.join()
                
                # If no Chinese was detected during streaming, still clean the final response
                if not chinese_detected and collected_response:
                    cleaned_response = self._clean_llm_response(collected_response, language='ar')
                    # If cleaning detected issues, send a warning as the final token
                    if " Warning" in cleaned_response:
                        yield "\n [Cleaned] Response contained unsupported content."
                
                logger.info("Arabic generation completed")
            else:
                # Non-streaming mode with stricter parameters
                with torch.no_grad():
                    # Create bad words filter
                    bad_words_ids = self._create_bad_words_filter(self.arabic_tokenizer, 'ar')
                    
                    generation_kwargs = {
                        **inputs,
                        "max_new_tokens": 150,     # Even stricter limit
                        "temperature": 0.1,        # Very low temperature
                        "top_p": 0.8,             # More restrictive
                        "do_sample": True,
                        "pad_token_id": self.arabic_tokenizer.eos_token_id,
                        "eos_token_id": self.arabic_tokenizer.eos_token_id,
                        "repetition_penalty": 2.0,  # Higher penalty
                        "no_repeat_ngram_size": 4   # Stricter n-gram
                    }
                    
                    # Add bad words filter if available
                    if bad_words_ids:
                        generation_kwargs["bad_words_ids"] = bad_words_ids
                    
                    outputs = self.arabic_llm.generate(**generation_kwargs)
                
                response = self.arabic_tokenizer.decode(outputs[0], skip_special_tokens=True)
                response = response.split("Answer (in Arabic, comprehensive):")[-1].strip() if "Answer (in Arabic, comprehensive):" in response else response[len(prompt):].strip()
                
                # Clean output: extract answer and sources
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
        """Generate response using OpenRouter API."""
        if not self.api_client:
            logger.warning("API client not configured. Please set OPENROUTER_API_KEY.")
            yield "API client not configured"
            return
        
        try:
            # Use same restrictions as local models - STRICTER
            max_tokens = 150  # Even more restrictive
            temperature = 0.1  # Very low temperature
            
            response = self.api_client.chat.completions.create(
                model=self.settings.DEFAULT_LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if stream:
                collected_response = ""
                chinese_detected = False
                
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        
                        # Early Chinese detection in API streaming
                        import re
                        if not chinese_detected:
                            chinese_in_token = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f]', token))
                            if chinese_in_token > 0:
                                chinese_detected = True
                                logger.warning(f"[API-{language}] Chinese character detection in API response")
                                yield " Warning: API model generated response in unsupported language."
                                return
                        
                        collected_response += token
                        if len(collected_response) > 2000:
                            logger.warning(f"[API-{language}] API response too long, stopping")
                            break
                            
                        yield token
            else:
                if hasattr(response.choices[0].message, 'content'):
                    api_response = response.choices[0].message.content
                    # Clean API response too
                    cleaned_response = self._clean_llm_response(api_response, language)
                    yield cleaned_response
                else:
                    yield "No response from API"
                
        except Exception as e:
            logger.error(f"Error calling API LLM: {e}", exc_info=True)
            yield f"Error: {str(e)}"
