"""
Tests for Validators
"""
import unittest
from validators.content_validators import (
    MarketValidator, CompanyValidator, SWOTValidator
)


class TestValidators(unittest.TestCase):
    """Test cases for validators"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.market_validator = MarketValidator()
        self.company_validator = CompanyValidator()
        self.swot_validator = SWOTValidator()
    
    def test_market_validator_short_content(self):
        """Test market validator with short content"""
        short_content = "too short"
        is_valid, message = self.market_validator.validate(short_content)
        self.assertFalse(is_valid)
    
    def test_market_validator_valid_content(self):
        """Test market validator with valid content"""
        valid_content = "배터리 시장은 매우 크고 빠르게 성장하고 있습니다. " * 20
        is_valid, message = self.market_validator.validate(valid_content)
        self.assertTrue(is_valid)
    
    def test_swot_validator_missing_keywords(self):
        """Test SWOT validator missing keywords"""
        content = "This is just random content without SWOT keywords"
        is_valid, message = self.swot_validator.validate(content)
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
