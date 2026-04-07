"""
Content validators for each agent output
"""
from typing import Tuple, Any
from validators.base_validator import BaseValidator


class MarketValidator(BaseValidator):
    """Validates market research agent output"""
    
    def validate(self, content: Any) -> Tuple[bool, str]:
        """Validate market research content"""
        if isinstance(content, dict):
            text = str(content.get("result", ""))
        else:
            text = str(content)
        
        validators = [
            lambda: self.check_text_length(text),
            lambda: self.check_minimum_sentences(text),
        ]
        
        is_valid, messages = self.validate_all(validators)
        message = " | ".join(messages)
        
        if is_valid:
            self.logger.info("Market research validation passed")
        else:
            self.logger.warning(f"Market research validation failed: {message}")
        
        return is_valid, message


class CompanyValidator(BaseValidator):
    """Validates company research agent output"""
    
    def validate(self, content: Any) -> Tuple[bool, str]:
        """Validate company research content"""
        if isinstance(content, dict):
            lg_text = str(content.get("lg_result", ""))
            catl_text = str(content.get("catl_result", ""))
            both_text = lg_text + catl_text
        else:
            both_text = str(content)
        
        validators = [
            lambda: self.check_text_length(both_text),
            lambda: self.check_minimum_sentences(both_text),
        ]
        
        is_valid, messages = self.validate_all(validators)
        message = " | ".join(messages)
        
        if is_valid:
            self.logger.info("Company research validation passed")
        else:
            self.logger.warning(f"Company research validation failed: {message}")
        
        return is_valid, message


class SWOTValidator(BaseValidator):
    """Validates SWOT analysis agent output"""
    
    def validate(self, content: Any) -> Tuple[bool, str]:
        """Validate SWOT analysis content"""
        if isinstance(content, dict):
            text = str(content.get("result", ""))
        else:
            text = str(content)
        
        # Additional SWOT-specific checks
        swot_keywords = ["강점", "약점", "기회", "위협"]
        has_keywords = sum(1 for kw in swot_keywords if kw in text)
        
        validators = [
            lambda: self.check_text_length(text),
            lambda: self.check_minimum_sentences(text),
            lambda: (has_keywords >= 4, f"SWOT keywords found: {has_keywords}/4" if has_keywords == 4 else f"Missing SWOT keywords: {4-has_keywords}")
        ]
        
        is_valid, messages = self.validate_all(validators)
        message = " | ".join(messages)
        
        if is_valid:
            self.logger.info("SWOT validation passed")
        else:
            self.logger.warning(f"SWOT validation failed: {message}")
        
        return is_valid, message


class ReportValidator(BaseValidator):
    """Validates final report output"""
    
    def validate(self, content: Any) -> Tuple[bool, str]:
        """Validate final report content"""
        if isinstance(content, dict):
            text = str(content.get("result", ""))
        else:
            text = str(content)
        
        # Report should be longer
        report_validators = [
            lambda: (len(text) >= 2000, f"Report length: {len(text)} (recommended >= 2000)"),
            lambda: self.check_minimum_sentences(text, min_count=30),
        ]
        
        is_valid, messages = self.validate_all(report_validators)
        message = " | ".join(messages)
        
        if is_valid:
            self.logger.info("Report validation passed")
        else:
            self.logger.warning(f"Report validation failed: {message}")
        
        return is_valid, message
