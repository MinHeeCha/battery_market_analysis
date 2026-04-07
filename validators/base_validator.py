"""
Base validator class - defines common validation interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from shared.logger import get_logger
from shared.constants import MIN_TEXT_LENGTH, MAX_TEXT_LENGTH, MIN_SENTENCES

logger = get_logger(__name__)


class BaseValidator(ABC):
    """
    Abstract base class for all validators.
    Each agent output is validated before proceeding to next phase.
    """
    
    def __init__(self, min_length: int = MIN_TEXT_LENGTH, max_length: int = MAX_TEXT_LENGTH):
        self.min_length = min_length
        self.max_length = max_length
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def validate(self, content: Any) -> Tuple[bool, str]:
        """
        Validate content.
        
        Args:
            content: Content to validate (can be str, dict, or structured object)
            
        Returns:
            Tuple of (is_valid, message)
        """
        pass
    
    def check_text_length(self, text: str) -> Tuple[bool, str]:
        """Check if text meets length requirements"""
        if not text or len(text.strip()) == 0:
            return False, "Content is empty"
        if len(text) < self.min_length:
            return False, f"Content too short: {len(text)} < {self.min_length}"
        if len(text) > self.max_length:
            return False, f"Content too long: {len(text)} > {self.max_length}"
        return True, "Length check passed"
    
    def check_required_fields(self, data: Dict[str, Any], fields: list) -> Tuple[bool, str]:
        """Check if required fields are present and non-empty"""
        missing = [f for f in fields if f not in data or not data[f]]
        if missing:
            return False, f"Missing required fields: {missing}"
        return True, "All required fields present"
    
    def check_minimum_sentences(self, text: str, min_count: int = MIN_SENTENCES) -> Tuple[bool, str]:
        """Check if text has minimum number of sentences"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) < min_count:
            return False, f"Too few sentences: {len(sentences)} < {min_count}"
        return True, "Sentence count check passed"
    
    def validate_all(self, validators: list) -> Tuple[bool, list]:
        """Run multiple validators and return combined result"""
        results = []
        for validator in validators:
            is_valid, message = validator()
            results.append((is_valid, message))
        
        all_valid = all(result[0] for result in results)
        messages = [msg for _, msg in results]
        
        return all_valid, messages
