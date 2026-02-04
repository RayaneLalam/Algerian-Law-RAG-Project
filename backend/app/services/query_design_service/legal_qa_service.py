import logging
import traceback
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class LegalQAService:
    """
    Main service for legal question answering
    Handles bilingual queries (French + Arabic)
    
    SECURITY ENHANCED: Dangerous queries are blocked IMMEDIATELY
    without LLM enhancement or further processing
    """
    
    def __init__(self, config_path=None):
        """Initialize the legal QA service"""
        self._setup_logging()
        self.logger.info("Initializing Legal QA Service")
        
        # Load configuration
        from .legal_qa_config import LegalQAConfig
        self.config = LegalQAConfig(config_path)
        
        # Initialize LLM (your teammate's model) - will be set externally
        self.model = None
        
        # Initialize security components
        from .legal_qa_sec import SecurityFilter, RateLimiter, SecurityAuditor
        
        self.security_filter = SecurityFilter(self.config)
        self.rate_limiter = RateLimiter(
            self.config.rate_limit_max_requests,
            self.config.rate_limit_window_seconds
        )
        self.security_auditor = SecurityAuditor()
        
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
        
        CRITICAL: Dangerous queries are REJECTED IMMEDIATELY without enhancement
        
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
            "security_severity": None,
            "rate_limited": False
        }
        
        # Step 1: Check rate limiting FIRST
        if user_id and not self.rate_limiter.check_rate_limit(user_id):
            result["is_secure"] = False
            result["rate_limited"] = True
            result["security_reason"] = "Rate limit exceeded"
            result["security_severity"] = "high"
            self.logger.warning(f"Rate limit exceeded for user {user_id}")
            return result
        
        # Step 2: CRITICAL - Rule-based security check (PRIMARY GATE)
        security_check = self.security_filter.check_query_security(query)
        if not security_check["is_secure"]:
            # REJECTED - Do not proceed with ANY processing
            result["is_secure"] = False
            result["security_reason"] = security_check.get("reason")
            result["security_severity"] = security_check.get("severity", "high")
            
            # Log security violation
            self.security_auditor.log_security_violation(
                user_id or "anonymous",
                query,
                security_check.get("reason", "unknown"),
                f"Severity: {security_check.get('severity', 'unknown')}"
            )
            
            self.logger.warning(
                f"SECURITY BLOCK: User {user_id or 'anonymous'} | "
                f"Reason: {result['security_reason']} | "
                f"Severity: {result['security_severity']}"
            )
            
            # Return immediately - NO enhancement, NO LLM processing
            return result
        
        # Step 3: Detect language (only if query is secure)
        language = self.config.detect_language(query)
        result["language"] = language
        self.logger.info(f"Detected language: {language}")
        
        # Step 4: Enhance query with LLM (ONLY if secure and model available)
        # This is now SAFE because dangerous queries were already rejected
        try:
            if self.model:
                enhanced = self._enhance_query(query, language)
                if enhanced and enhanced != query:
                    result["processed_query"] = enhanced
        except Exception as e:
            self.logger.error(f"Query enhancement failed: {e}")
            # If enhancement fails, continue with original query
        
        # Step 5: LLM analysis for continuation (ONLY if conversation exists)
        if conversation_history and len(conversation_history) > 0:
            try:
                if self.model:
                    analysis = self._analyze_query_with_llm(
                        query, conversation_history, language
                    )
                    # Only update continuation flag from LLM analysis
                    # Security status is ONLY determined by rule-based filter above
                    if "is_continuation" in analysis:
                        result["is_continuation"] = analysis["is_continuation"]
            except Exception as e:
                self.logger.error(f"LLM analysis failed: {e}")
        
        return result
    
    def _enhance_query(self, query, language):
        """
        Enhance query clarity using LLM
        
        NOTE: This is only called for queries that passed security checks
        
        Args:
            query: Original query
            language: 'ar' or 'fr'
        
        Returns:
            str: Enhanced query
        """
        if not self.model:
            return query
            
        try:
            # Get language-specific prompt
            template = self.config.get_prompt_template(
                "preprocess_system_prompt",
                language
            )
            prompt = template.format(query=query)
            
            # Generate enhanced query using BilingualLLMService
            response_generator = self.model.generate_completion(
                prompt, 
                language=language,
                stream=False
            )
            
            # Consume the generator to get the actual text
            enhanced = ''.join(response_generator).strip()
            
            if enhanced and enhanced != query:
                self.logger.info(f"Enhanced query: {query[:50]}... -> {enhanced[:50]}...")
                return enhanced
            return query
            
        except Exception as e:
            self.logger.error(f"Enhancement error: {e}")
            return query
    
    def _analyze_query_with_llm(self, query, history, language):
        """
        Use LLM to analyze query for continuation detection
        
        NOTE: Security decisions are NOT made here - only continuation detection
        Rule-based security filter is the authoritative security gate
        
        Args:
            query: User query
            history: Conversation history
            language: 'ar' or 'fr'
        
        Returns:
            dict: Analysis results (only continuation flag)
        """
        if not self.model:
            return {}
            
        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(query, history, language)
            
            # Generate analysis using BilingualLLMService
            response_generator = self.model.generate_completion(
                prompt,
                language=language,
                stream=False
            )
            
            # Consume the generator to get the actual text
            response_text = ''.join(response_generator).strip()
            
            # Parse response - ONLY extract continuation flag
            result = {
                "is_continuation": "true" in response_text.lower().split("is_continuation:")[1].split("\n")[0] if "is_continuation:" in response_text else False
            }
            
            # Extract processed query if available
            if "processed_query:" in response_text:
                processed = response_text.split("processed_query:")[1].split("\n")[0].strip()
                if processed:
                    result["processed_query"] = processed
            
            return result
            
        except Exception as e:
            self.logger.error(f"LLM analysis error: {e}")
            return {}
    
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
        template = self.config.get_prompt_template("analysis_system_prompt", language)
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
                    "Limite de requêtes dépassée. Réessayez dans quelques instants." if query_result.get("language") == 'fr' 
                    else "تجاوز الحد المسموح. يرجى المحاولة بعد قليل.",
                    "rate_limited",
                    event_id,
                    query_result.get("language", "ar")
                )
            
            # Handle security violations
            if not query_result["is_secure"]:
                severity = query_result.get("security_severity", "high")
                self.logger.warning(
                    f"Security violation detected | Event: {event_id} | "
                    f"Severity: {severity} | Reason: {query_result.get('security_reason')}"
                )
                
                return self._build_error_response(
                    "Requête non autorisée. Veuillez reformuler votre question de manière appropriée." if query_result.get("language") == 'fr'
                    else "طلب غير مصرح به. يرجى إعادة صياغة سؤالك بشكل مناسب.",
                    "rejected",
                    event_id,
                    query_result.get("language", "ar")
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
            
            # Step 4: Generate answer
            if not self.model:
                raise Exception("LLM model not initialized")
            
            response_generator = self.model.generate_completion(
                prompt,
                language=language,
                stream=False
            )
            
            # Consume the generator to get the actual text
            answer_text = ''.join(response_generator).strip()
            
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
        template = self.config.get_prompt_template("answer_system_prompt", language)
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