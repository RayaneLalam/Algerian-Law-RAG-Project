from typing import TypedDict
import logging

logger = logging.getLogger(__name__)


class LanguageConfig(TypedDict):
    """Language-specific configuration."""
    language: str
    embedder_model: str
    index_path: str
    docs_path: str
    llm_model: str
    prompt_template_path: str
    max_tokens: int


class LanguageService:
    """Service for language detection and routing."""
    
    ARABIC_RANGE = ('\u0600', '\u06FF')
    FRENCH_REQUESTS = ['en francais', 'in french', 'بالفرنسية', 'answer in french', 
                       'repondre en francais', 'أجب بالفرنسية']
    ARABIC_REQUESTS = ['en arabe', 'in arabic', 'بالعربية', 'answer in arabic', 
                       'repondre en arabe', 'أجب بالعربية']
    
    @staticmethod
    def detect_script(text: str) -> str:
        """
        Detect if text is Arabic or French/Latin script.
        
        Args:
            text: Input text
            
        Returns:
            'arabic' or 'french' based on character prevalence
        """
        if not text:
            return 'french'
        
        arabic_chars = sum(
            1 for c in text 
            if LanguageService.ARABIC_RANGE[0] <= c <= LanguageService.ARABIC_RANGE[1]
        )
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars == 0:
            return 'french'
        
        arabic_ratio = arabic_chars / total_chars
        return 'arabic' if arabic_ratio > 0.5 else 'french'
    
    @staticmethod
    def detect_response_language(query: str) -> str:
        """
        Infer desired response language from query.
        
        Checks for explicit language requests before falling back to script detection.
        
        Args:
            query: User query
            
        Returns:
            'ar' or 'fr'
        """
        if not query:
            return 'fr'
        
        query_lower = query.lower()
        
        # Check for explicit French requests
        for req in LanguageService.FRENCH_REQUESTS:
            if req in query_lower:
                logger.debug(f"Explicit French request detected: '{req}'")
                return 'fr'
        
        # Check for explicit Arabic requests
        for req in LanguageService.ARABIC_REQUESTS:
            if req in query_lower:
                logger.debug(f"Explicit Arabic request detected: '{req}'")
                return 'ar'
        
        # Fall back to script detection
        script = LanguageService.detect_script(query)
        language = 'ar' if script == 'arabic' else 'fr'
        logger.debug(f"Auto-detected language based on script: {language}")
        return language
    
    @staticmethod
    def normalize_language(language: str) -> str:
        """
        Normalize language code to valid value.
        
        Args:
            language: Language code ('ar', 'fr', 'arabic', 'french', 'auto', etc.)
            
        Returns:
            'ar' or 'fr'
        """
        if not language:
            return 'fr'
        
        language = language.lower().strip()
        
        if language in ('ar', 'arabic', 'العربية'):
            return 'ar'
        elif language in ('fr', 'french', 'francais', 'français'):
            return 'fr'
        elif language == 'auto':
            return 'fr'
        else:
            logger.warning(f"Unknown language code '{language}', defaulting to French")
            return 'fr'
    
    @staticmethod
    def get_language_config(language: str) -> LanguageConfig:
        """
        Get language-specific configuration.
        
        Args:
            language: 'ar' or 'fr'
            
        Returns:
            LanguageConfig with model paths and settings
        """
        from app.config.settings import settings
        
        language = LanguageService.normalize_language(language)
        
        if language == 'ar':
            return LanguageConfig(
                language='ar',
                embedder_model=settings.ARABIC_EMBEDDING_MODEL,
                index_path=settings.ARABIC_INDEX_PATH,
                docs_path=settings.ARABIC_META_PATH,
                llm_model=settings.ARABIC_LLM_MODEL if settings.USE_LOCAL_LLMS else settings.DEFAULT_LLM_MODEL,
                prompt_template_path='./app/prompt_templates/qa_with_context_ar.txt',
                max_tokens=settings.MAX_NEW_TOKENS_AR
            )
        else:
            return LanguageConfig(
                language='fr',
                embedder_model=settings.FRENCH_EMBEDDING_MODEL,
                index_path=settings.FRENCH_INDEX_PATH,
                docs_path=settings.FRENCH_DOCS_PATH,
                llm_model=settings.FRENCH_LLM_MODEL if settings.USE_LOCAL_LLMS else settings.DEFAULT_LLM_MODEL,
                prompt_template_path='./app/prompt_templates/qa_with_context_fr.txt',
                max_tokens=settings.MAX_NEW_TOKENS_FR
            )
