import logging
import torch
from typing import Generator, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class BilingualLLMService:
    """
    Bilingual LLM service supporting both local and API-based inference.
    
    Routes requests to appropriate models (French Vigogne or Arabic Qwen2.5).
    Falls back to API if local models not available.
    """
    
    def __init__(self):
        from app.config.settings import settings
        
        self.settings = settings
        self.use_local_llms = settings.USE_LOCAL_LLMS
        self.device = settings.DEVICE
        
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
                
                self.api_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.OPENROUTER_API_KEY,
                )
                logger.info("OpenRouter API client initialized for LLM fallback")
            except TypeError as te:
                if 'proxies' in str(te):
                    logger.warning(f"Proxies parameter incompatibility: {te}. Retrying without proxy handling.")
                    try:
                        self.api_client = OpenAI(
                            base_url="https://openrouter.ai/api/v1",
                            api_key=settings.OPENROUTER_API_KEY,
                        )
                    except Exception as retry_err:
                        logger.error(f"Failed to initialize OpenRouter API client on retry: {retry_err}")
                        self.api_client = None
                else:
                    logger.error(f"TypeError initializing OpenRouter API client: {te}")
                    self.api_client = None
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
    
    def _load_french_llm(self):
        """Load French LLM (Vigogne-2-7B) with lazy loading."""
        if self.french_llm is not None:
            return
        
        logger.info(f"Loading French LLM: {self.settings.FRENCH_LLM_MODEL}")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            
            self.french_tokenizer = AutoTokenizer.from_pretrained(self.settings.FRENCH_LLM_MODEL)
            
            if self.settings.USE_4BIT_QUANTIZATION and torch.cuda.is_available():
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
                    trust_remote_code=True
                )
            else:
                self.french_llm = AutoModelForCausalLM.from_pretrained(
                    self.settings.FRENCH_LLM_MODEL,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True
                )
            
            logger.info("French LLM loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load French LLM: {e}", exc_info=True)
            self.french_llm = None
    
    def _load_arabic_llm(self):
        """Load Arabic LLM (Qwen2.5-7B) with lazy loading."""
        if self.arabic_llm is not None:
            return
        
        logger.info(f"Loading Arabic LLM: {self.settings.ARABIC_LLM_MODEL}")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            
            self.arabic_tokenizer = AutoTokenizer.from_pretrained(self.settings.ARABIC_LLM_MODEL)
            
            if self.settings.USE_4BIT_QUANTIZATION and torch.cuda.is_available():
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
                    trust_remote_code=True
                )
            else:
                self.arabic_llm = AutoModelForCausalLM.from_pretrained(
                    self.settings.ARABIC_LLM_MODEL,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True
                )
            
            logger.info("Arabic LLM loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Arabic LLM: {e}", exc_info=True)
            self.arabic_llm = None
    
    def _generate_french_local(self, prompt: str, stream: bool = False) -> Generator[str, None, None]:
        """Generate French response using local Vigogne model."""
        self._load_french_llm()
        
        if self.french_llm is None:
            logger.warning("French LLM not available, falling back to API")
            yield from self._generate_api(prompt, 'fr', stream)
            return
        
        try:
            inputs = self.french_tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.french_llm.generate(
                    **inputs,
                    max_new_tokens=self.settings.MAX_NEW_TOKENS_FR,
                    temperature=self.settings.LLM_TEMPERATURE,
                    top_p=0.95,
                    do_sample=True,
                    pad_token_id=self.french_tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            response = self.french_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if "<|assistant|>:" in response:
                response = response.split("<|assistant|>:")[-1].strip()
            else:
                response = response[len(prompt):].strip()
            
            if stream:
                for word in response.split():
                    yield word + " "
            else:
                yield response
                
        except Exception as e:
            logger.error(f"Error generating French response: {e}", exc_info=True)
            yield f"Error generating French response: {str(e)}"
    
    def _generate_arabic_local(self, prompt: str, stream: bool = False) -> Generator[str, None, None]:
        """Generate Arabic response using local Qwen model."""
        self._load_arabic_llm()
        
        if self.arabic_llm is None:
            logger.warning("Arabic LLM not available, falling back to API")
            yield from self._generate_api(prompt, 'ar', stream)
            return
        
        try:
            inputs = self.arabic_tokenizer(prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.arabic_llm.generate(
                    **inputs,
                    max_new_tokens=self.settings.MAX_NEW_TOKENS_AR,
                    temperature=self.settings.LLM_TEMPERATURE,
                    repetition_penalty=1.1
                )
            
            response = self.arabic_tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.split("Answer (in Arabic, comprehensive):")[-1].strip() if "Answer (in Arabic, comprehensive):" in response else response[len(prompt):].strip()
            
            if stream:
                for word in response.split():
                    yield word + " "
            else:
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
            response = self.api_client.chat.completions.create(
                model=self.settings.DEFAULT_LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=512
            )
            
            if stream:
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                if hasattr(response.choices[0].message, 'content'):
                    yield response.choices[0].message.content
                else:
                    yield "No response from API"
                
        except Exception as e:
            logger.error(f"Error calling API LLM: {e}", exc_info=True)
            yield f"Error: {str(e)}"
