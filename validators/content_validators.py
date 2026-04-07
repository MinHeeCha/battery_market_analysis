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
        """Validate structured SWOT analysis content"""
        result = content.get("result") if isinstance(content, dict) else content
        if not isinstance(result, dict):
            return False, "SWOT result must be a dict with lg_swot/catl_swot/comparative_swot"

        lg_swot = result.get("lg_swot")
        catl_swot = result.get("catl_swot")
        comparative_swot = result.get("comparative_swot", "")

        required_fields = ["strengths", "weaknesses", "opportunities", "threats"]

        def check_company_swot(name: str, swot: Any) -> Tuple[bool, str]:
            if not isinstance(swot, dict):
                return False, f"{name} SWOT must be dict"
            missing = [f for f in required_fields if f not in swot]
            if missing:
                return False, f"{name} missing fields: {', '.join(missing)}"
            empty = [f for f in required_fields if not isinstance(swot.get(f), list) or len(swot.get(f, [])) == 0]
            if empty:
                return False, f"{name} empty quadrants: {', '.join(empty)}"
            return True, f"{name} structure OK"

        lg_ok, lg_msg = check_company_swot("LG", lg_swot)
        catl_ok, catl_msg = check_company_swot("CATL", catl_swot)
        comp_ok = bool(str(comparative_swot).strip())

        combined_text = f"{lg_swot}\n{catl_swot}\n{comparative_swot}"
        validators = [
            lambda: (lg_ok, lg_msg),
            lambda: (catl_ok, catl_msg),
            lambda: (comp_ok, "comparative_swot exists" if comp_ok else "comparative_swot is empty"),
            lambda: self.check_text_length(combined_text),
            lambda: self.check_minimum_sentences(str(comparative_swot), min_count=3),
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
