import logging
import traceback
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Import your LLM and config
# from app.services.llm_service.factory import create_llm
# from legal_qa_config import LegalQAConfig
# from qa_sec import SecurityFilter, RateLimiter, SecurityAuditor


class LegalQAService:
    """
    Main service for legal question answering
    Handles bilingual queries (French + Arabic)
    """
    
    def __init__(self, config_path=None):
        """Initialize the legal QA service"""
        self._setup_logging()
        self.logger.info("Initializing Legal QA Service")
        
        # Load configuration
        # self.config = LegalQAConfig(config_path)
        
        # Initialize LLM (your teammate's model)
        # self.model = create_llm()
        
        # Initialize security components
        # self.security_filter = SecurityFilter(self.config)
        # self.rate_limiter = RateLimiter(
        #     self.config.rate_limit_max_requests,
        #     self.config.rate_limit_window_seconds
        # )
        # self.security_auditor = SecurityAuditor()
        
        self.logger.info("Legal QA Service initialized")
    
    def _setup_logging(self):
        """Set up logging"""
        self.logger = logging.getLogger("legal_qa.service")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def preprocess_query(self, query, conversation_history=None, user_id=None):
        """
        Process user query with security and language detection
        
        Args:
            query: User question (French or Arabic)
            conversation_history: Previous messages
            user_id: User identifier
        
        Returns:
            dict: Processed query with metadata
        """
        result = {
            "raw_query": query,
            "processed_query": query,
            "language": None,
            "is_continuation": False,
            "is_secure": True,
            "security_reason": None,
            "rate_limited": False
        }
        
        # Step 1: Detect language
        language = self.config.detect_language(query)
        result["language"] = language
        self.logger.info(f"Detected language: {language}")
        
        # Step 2: Check rate limiting
        if user_id and not self.rate_limiter.check_rate_limit(user_id):
            result["is_secure"] = False
            result["rate_limited"] = True
            result["security_reason"] = "Rate limit exceeded"
            return result
        
        # Step 3: Security check (rule-based)
        security_check = self.security_filter.check_query_security(query)
        if not security_check["is_secure"]:
            result["is_secure"] = False
            result["security_reason"] = security_check.get("reason")
            return result
        
        # Step 4: Enhance query with LLM (optional)
        try:
            enhanced = self._enhance_query(query, language)
            if enhanced:
                result["processed_query"] = enhanced
        except Exception as e:
            self.logger.error(f"Query enhancement failed: {e}")
        
        # Step 5: LLM security analysis (if conversation exists)
        if conversation_history and len(conversation_history) > 0:
            try:
                analysis = self._analyze_query_with_llm(
                    query, conversation_history, language
                )
                result.update(analysis)
            except Exception as e:
                self.logger.error(f"LLM analysis failed: {e}")
        
        return result
    
    def _enhance_query(self, query, language):
        """
        Enhance query clarity using LLM
        
        Args:
            query: Original query
            language: 'ar' or 'fr'
        
        Returns:
            str: Enhanced query
        """
        try:
            # Get language-specific prompt
            template = self.config.get_prompt_template(
                "preprocess_system", 
                language
            )
            prompt = template.format(query=query)
            
            # Generate enhanced query
            response = self.model.generate_content(
                prompt, 
                system_prompt=template
            )
            enhanced = response.text.strip()
            
            if enhanced and enhanced != query:
                return enhanced
            return query
            
        except Exception as e:
            self.logger.error(f"Enhancement error: {e}")
            return query
    
    def _analyze_query_with_llm(self, query, history, language):
        """
        Use LLM to analyze query security and continuation
        
        Args:
            query: User query
            history: Conversation history
            language: 'ar' or 'fr'
        
        Returns:
            dict: Analysis results
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(query, history, language)
        
        # Get system prompt for analysis
        system_prompt = self.config.get_prompt_template(
            "analysis_system",
            language
        )
        
        # Generate analysis
        response = self.model.generate_content(prompt, system_prompt=system_prompt)
        response_text = response.text
        
        # Parse response
        result = {
            "is_continuation": "true" in response_text.lower().split("is_continuation:")[1].split("\n")[0] if "is_continuation:" in response_text else False,
            "is_secure": not ("false" in response_text.lower().split("is_secure:")[1].split("\n")[0]) if "is_secure:" in response_text else True
        }
        
        # Extract security reason
        if not result["is_secure"] and "security_reason:" in response_text:
            result["security_reason"] = response_text.split("security_reason:")[1].split("\n")[0].strip()
        
        # Extract processed query
        if "processed_query:" in response_text:
            processed = response_text.split("processed_query:")[1].split("\n")[0].strip()
            if processed:
                result["processed_query"] = processed
        
        return result
    
    def _build_analysis_prompt(self, query, history, language):
        """Build prompt for query analysis"""
        # Format history
        history_text = ""
        for msg in history[-self.config.max_history_items:]:
            role = "المستخدم" if msg["role"] == "user" else "المساعد"
            if language == 'fr':
                role = "Utilisateur" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n\n"
        
        # Get template and fill
        template = self.config.get_prompt_template("analysis_system", language)
        return template.format(history=history_text, query=query)
    
    def generate_answer(self, query, context_chunks, conversation_history=None, user_id=None):
        """
        Generate answer from legal documents
        
        Args:
            query: User question
            context_chunks: Relevant legal document excerpts (from your JSON data)
            conversation_history: Previous messages
            user_id: User identifier
        
        Returns:
            dict: Answer and metadata
        """
        event_id = None
        
        try:
            # Step 1: Preprocess query
            query_result = self.preprocess_query(query, conversation_history, user_id)
            
            # Log query
            event_id = self.security_auditor.log_query(
                user_id or "anonymous",
                query,
                "secure" if query_result["is_secure"] else "rejected"
            )
            
            # Handle rate limiting
            if query_result.get("rate_limited"):
                return self._build_error_response(
                    "Rate limit exceeded" if query_result["language"] == 'fr' 
                    else "تجاوز الحد المسموح",
                    "rate_limited",
                    event_id,
                    query_result["language"]
                )
            
            # Handle security violations
            if not query_result["is_secure"]:
                return self._build_error_response(
                    "Requête non autorisée" if query_result["language"] == 'fr'
                    else "طلب غير مصرح به",
                    "rejected",
                    event_id,
                    query_result["language"]
                )
            
            # Step 2: Get processed query and language
            processed_query = query_result["processed_query"]
            language = query_result["language"]
            is_continuation = query_result["is_continuation"]
            
            # Step 3: Build answer prompt
            prompt = self._build_answer_prompt(
                processed_query,
                context_chunks,
                conversation_history,
                is_continuation,
                language
            )
            
            # Get system prompt for answering
            system_prompt = self.config.get_prompt_template(
                "answer_system",
                language
            )
            
            # Step 4: Generate answer
            response = self.model.generate_content(prompt, system_prompt=system_prompt)
            answer_text = response.text
            
            # Log success
            self.security_auditor.log_response(
                user_id or "anonymous",
                event_id,
                "success"
            )
            
            return {
                'answer': answer_text,
                'status': 'success',
                'language': language,
                'is_continuation': is_continuation,
                'event_id': event_id,
                'raw_query': query,
                'processed_query': processed_query
            }
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            self.logger.debug(traceback.format_exc())
            
            if event_id:
                self.security_auditor.log_response(
                    user_id or "anonymous",
                    event_id,
                    "error"
                )
            
            # Generate error ID
            error_id = hashlib.md5(
                f"{str(e)}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:8]
            
            language = query_result.get("language", "ar") if 'query_result' in locals() else "ar"
            
            return self._build_error_response(
                f"Erreur système (Réf: {error_id})" if language == 'fr'
                else f"خطأ في النظام (مرجع: {error_id})",
                "error",
                event_id,
                language,
                error_id
            )
    
    def _build_answer_prompt(self, query, context_chunks, history, is_continuation, language):
        """
        Build prompt for answer generation
        
        Args:
            query: Processed query
            context_chunks: Legal document excerpts
            history: Conversation history
            is_continuation: Whether query continues conversation
            language: 'ar' or 'fr'
        
        Returns:
            str: Formatted prompt
        """
        # Format conversation context
        conversation_context = ""
        if history and len(history) > 0:
            if language == 'fr':
                conversation_context = "Contexte de conversation précédent:\n\n"
                for msg in history[-self.config.max_history_items:]:
                    role = "Utilisateur" if msg["role"] == "user" else "Assistant"
                    conversation_context += f"{role}: {msg['content']}\n\n"
            else:
                conversation_context = "سياق المحادثة السابقة:\n\n"
                for msg in history[-self.config.max_history_items:]:
                    role = "المستخدم" if msg["role"] == "user" else "المساعد"
                    conversation_context += f"{role}: {msg['content']}\n\n"
        
        # Continuation note
        continuation_note = ""
        if is_continuation:
            continuation_note = (
                "Cette question fait suite à la conversation précédente. "
                "Veuillez répondre en tenant compte du contexte.\n\n"
                if language == 'fr' else
                "هذا السؤال هو استمرار للمحادثة السابقة. "
                "يرجى الإجابة مع مراعاة السياق.\n\n"
            )
        
        # Format context chunks
        formatted_chunks = ""
        for i, chunk in enumerate(context_chunks, 1):
            if language == 'fr':
                formatted_chunks += f"Document {i}:\n{chunk}\n\n"
            else:
                formatted_chunks += f"المستند {i}:\n{chunk}\n\n"
        
        # Get template and fill
        template = self.config.get_prompt_template("answer_system", language)
        return template.format(
            conversation_context=conversation_context,
            query=query,
            continuation_note=continuation_note,
            context_chunks=formatted_chunks
        )
    
    def _build_error_response(self, message, status, event_id, language, error_id=None):
        """Build standardized error response"""
        response = {
            'answer': message,
            'status': status,
            'language': language,
            'event_id': event_id
        }
        if error_id:
            response['error_id'] = error_id
        return response