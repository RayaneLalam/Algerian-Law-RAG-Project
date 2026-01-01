import re
import time
import logging
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta


class SecurityFilter:
    """
    Security filter to detect and prevent prompt injection
    and filter restricted content for legal chatbot
    """
    
    def __init__(self, config):
        """
        Initialize security filter
        
        Args:
            config: LegalQAConfig instance with security settings
        """
        self.config = config
        self.logger = logging.getLogger("legal_qa.security")
        
    def check_query_security(self, query):
        """
        Apply rule-based security checks to the query
        
        Args:
            query: User query text (French or Arabic)
            
        Returns:
            dict: Security status with flags and reasons
        """
        # Basic validation
        if not query or not isinstance(query, str):
            return {
                "is_secure": False, 
                "reason": "Invalid query format"
            }
        
        # Strip whitespace
        query = query.strip()
        if not query:
            return {
                "is_secure": False,
                "reason": "Empty query"
            }
            
        # Length check
        if len(query) > self.config.max_query_length:
            self.logger.warning(f"Query exceeds max length: {len(query)}")
            return {
                "is_secure": False, 
                "reason": "Query exceeds maximum allowed length"
            }
            
        # Check for potential prompt injection patterns
        for pattern in self.config.security_patterns['blocklist']:
            try:
                if re.search(pattern, query, re.IGNORECASE):
                    self.logger.warning(f"Blocklist pattern matched in query")
                    return {
                        "is_secure": False,
                        "reason": "Potential security violation detected"
                    }
            except Exception as e:
                self.logger.error(f"Error checking security pattern: {e}")
                
        # Check for SQL injection attempts
        sql_keywords = [
            'select ', 'insert ', 'update ', 'delete ', 'drop ', 
            '--', '/*', '*/', ';--', 'union ', 'exec('
        ]
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in sql_keywords):
            self.logger.warning(f"SQL injection pattern detected in query")
            return {
                "is_secure": False,
                "reason": "Potential SQL injection attempt"
            }
        
        # Check for script injection (XSS)
        xss_patterns = [
            r'<script', r'javascript:', r'onerror=', r'onclick=',
            r'<iframe', r'<embed', r'<object'
        ]
        for pattern in xss_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                self.logger.warning(f"XSS pattern detected in query")
                return {
                    "is_secure": False,
                    "reason": "Potential XSS attempt detected"
                }
            
        return {"is_secure": True}
        
    def scrub_sensitive_data(self, text):
        """
        Redact potentially sensitive information from text
        
        Args:
            text: Text to scrub
            
        Returns:
            str: Scrubbed text with sensitive data redacted
        """
        if not text:
            return text
            
        scrubbed_text = text
        
        # Redact patterns from config
        for pattern in self.config.security_patterns['sensitive_data']:
            try:
                scrubbed_text = re.sub(
                    pattern, 
                    '[DONNÉES_SENSIBLES]',  # French/Arabic neutral
                    scrubbed_text, 
                    flags=re.IGNORECASE
                )
            except Exception as e:
                self.logger.error(f"Error in sensitive data pattern: {e}")
        
        # Additional legal-specific scrubbing
        # Redact case numbers that might be sensitive
        scrubbed_text = re.sub(
            r'\b\d{2,4}/\d{2,4}\b',  # Case numbers like 123/2024
            '[NUMÉRO_AFFAIRE]',
            scrubbed_text
        )
        
        # Redact potential client names (simple heuristic)
        # This is basic - you may want more sophisticated NER
        scrubbed_text = re.sub(
            r'\b(?:Monsieur|Madame|M\.|Mme)\s+[A-Z][a-z]+\b',
            '[NOM_CLIENT]',
            scrubbed_text
        )
        
        return scrubbed_text


class RateLimiter:
    """
    Rate limiting to prevent abuse
    Adapted for lawyer usage patterns
    """
    
    def __init__(self, max_requests=20, time_window=60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum allowed requests per time window
            time_window: Time window in seconds (default 60 = 1 minute)
        """
        self.request_history = defaultdict(lambda: deque())
        self.max_requests = max_requests
        self.time_window = time_window
        self.logger = logging.getLogger("legal_qa.rate_limiter")
        
        # Track rate limit violations for analytics
        self.violations = defaultdict(int)
        
    def check_rate_limit(self, user_id):
        """
        Check if a user has exceeded their rate limit
        
        Args:
            user_id: Identifier for the user (can be email, session_id, etc.)
            
        Returns:
            bool: True if user is within limits, False if rate limit exceeded
        """
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.time_window)
        
        # Clear old requests outside the time window
        self.request_history[user_id] = deque(
            t for t in self.request_history[user_id] if t > cutoff_time
        )
        
        # Check if user has exceeded rate limit
        if len(self.request_history[user_id]) >= self.max_requests:
            self.violations[user_id] += 1
            self.logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{len(self.request_history[user_id])} requests in {self.time_window}s window "
                f"(violation #{self.violations[user_id]})"
            )
            return False
            
        # Add current request
        self.request_history[user_id].append(now)
        return True
    
    def get_remaining_requests(self, user_id):
        """
        Get number of remaining requests for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Number of requests remaining in current window
        """
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.time_window)
        
        # Count valid requests
        valid_requests = sum(
            1 for t in self.request_history[user_id] if t > cutoff_time
        )
        
        return max(0, self.max_requests - valid_requests)
    
    def reset_user(self, user_id):
        """
        Reset rate limit for a specific user (admin function)
        
        Args:
            user_id: User identifier
        """
        if user_id in self.request_history:
            del self.request_history[user_id]
            self.logger.info(f"Rate limit reset for user {user_id}")


class SecurityAuditor:
    """
    Security auditing and logging
    Tracks all queries and responses for compliance and debugging
    """
    
    def __init__(self):
        """Initialize security auditor"""
        self.logger = logging.getLogger("legal_qa.audit")
        
        # Store recent events in memory (last 1000)
        self.recent_events = deque(maxlen=1000)
        
    def log_query(self, user_id, query, status, language=None):
        """
        Log a user query with security status
        
        Args:
            user_id: User identifier
            query: User query
            status: Security status ('secure', 'rejected', etc.)
            language: Detected language ('ar' or 'fr')
            
        Returns:
            str: Event ID for tracking
        """
        event_id = f"{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        
        # Truncate query for logging (privacy)
        safe_query = query[:100] + ("..." if len(query) > 100 else "")
        
        # Create event record
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "type": "query",
            "status": status,
            "language": language,
            "query_length": len(query)
        }
        
        self.recent_events.append(event)
        
        # Log to file/console
        lang_info = f" | Lang: {language}" if language else ""
        self.logger.info(
            f"QUERY [{event_id}] User: {user_id} | Status: {status}{lang_info} | "
            f"Query: {safe_query}"
        )
        
        return event_id
        
    def log_response(self, user_id, event_id, status, response_length=None):
        """
        Log a response with security information
        
        Args:
            user_id: User identifier
            event_id: Event ID from the query log
            status: Response status ('success', 'error', 'rejected')
            response_length: Length of response in characters
        """
        timestamp = datetime.now().isoformat()
        
        # Create event record
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "type": "response",
            "status": status,
            "response_length": response_length
        }
        
        self.recent_events.append(event)
        
        # Log to file/console
        length_info = f" | Length: {response_length}" if response_length else ""
        self.logger.info(
            f"RESPONSE [{event_id}] User: {user_id} | Status: {status}{length_info}"
        )
    
    def log_security_violation(self, user_id, query, violation_type, details=None):
        """
        Log a security violation for monitoring
        
        Args:
            user_id: User identifier
            query: Offending query
            violation_type: Type of violation (e.g., 'prompt_injection', 'sql_injection')
            details: Additional details about the violation
        """
        event_id = f"SEC-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        
        # Truncate query
        safe_query = query[:100] + ("..." if len(query) > 100 else "")
        
        # Create event record
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "type": "security_violation",
            "violation_type": violation_type,
            "details": details
        }
        
        self.recent_events.append(event)
        
        # Log with WARNING level
        self.logger.warning(
            f"SECURITY VIOLATION [{event_id}] User: {user_id} | "
            f"Type: {violation_type} | Query: {safe_query}"
        )
        
        if details:
            self.logger.warning(f"  Details: {details}")
    
    def get_user_statistics(self, user_id):
        """
        Get statistics for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: User statistics
        """
        user_events = [e for e in self.recent_events if e.get('user_id') == user_id]
        
        queries = [e for e in user_events if e.get('type') == 'query']
        violations = [e for e in user_events if e.get('type') == 'security_violation']
        
        return {
            "user_id": user_id,
            "total_queries": len(queries),
            "security_violations": len(violations),
            "languages": {
                "ar": sum(1 for e in queries if e.get('language') == 'ar'),
                "fr": sum(1 for e in queries if e.get('language') == 'fr')
            },
            "statuses": {
                "secure": sum(1 for e in queries if e.get('status') == 'secure'),
                "rejected": sum(1 for e in queries if e.get('status') == 'rejected')
            }
        }
    
    def get_recent_events(self, limit=100, event_type=None):
        """
        Get recent events for monitoring
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            
        Returns:
            list: Recent events
        """
        events = list(self.recent_events)
        
        if event_type:
            events = [e for e in events if e.get('type') == event_type]
        
        return events[-limit:]


class ContentValidator:
    """
    Validate legal content for quality and completeness
    (Optional - for additional quality checks)
    """
    
    def __init__(self):
        """Initialize content validator"""
        self.logger = logging.getLogger("legal_qa.validator")
    
    def validate_legal_citation(self, text):
        """
        Check if text contains proper legal citations
        
        Args:
            text: Text to validate
            
        Returns:
            dict: Validation results
        """
        # French legal citation patterns
        fr_patterns = [
            r'Article\s+\d+',
            r'Code\s+(?:civil|pénal|de commerce)',
            r'Loi\s+n°\s*\d+[-/]\d+'
        ]
        
        # Arabic legal citation patterns
        ar_patterns = [
            r'المادة\s+\d+',
            r'القانون\s+رقم\s+\d+',
            r'المرسوم\s+رقم\s+\d+'
        ]
        
        fr_citations = sum(
            len(re.findall(pattern, text, re.IGNORECASE)) 
            for pattern in fr_patterns
        )
        ar_citations = sum(
            len(re.findall(pattern, text)) 
            for pattern in ar_patterns
        )
        
        total_citations = fr_citations + ar_citations
        
        return {
            "has_citations": total_citations > 0,
            "citation_count": total_citations,
            "french_citations": fr_citations,
            "arabic_citations": ar_citations
        }
    
    def check_response_quality(self, response, min_length=50):
        """
        Basic quality check for responses
        
        Args:
            response: Generated response text
            min_length: Minimum acceptable length
            
        Returns:
            dict: Quality metrics
        """
        return {
            "is_valid": len(response) >= min_length,
            "length": len(response),
            "has_structure": any(marker in response for marker in ['**', '##', '-', '1.']),
            "has_citations": self.validate_legal_citation(response)["has_citations"]
        }