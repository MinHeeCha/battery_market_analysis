"""
Constants for Battery Analysis System
"""

# Agent names
AGENT_MARKET = "market_research"
AGENT_COMPANY = "company_research"
AGENT_SWOT = "swot_analysis"
AGENT_REPORT = "report_writer"

# Phase names
PHASE_INIT = "init"
PHASE_MARKET = "market_research"
PHASE_COMPANY = "company_research"
PHASE_SWOT = "swot_analysis"
PHASE_REPORT = "report_writing"
PHASE_VALIDATION = "validation"
PHASE_EXPORT = "export"

# Validation constants
MIN_TEXT_LENGTH = 500  # Minimum characters per output section
MAX_TEXT_LENGTH = 5000  # Maximum characters per output section
MIN_SENTENCES = 10  # Minimum sentences

# Retry constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2

# Companies
COMPANY_LG = "LG에너지솔루션"
COMPANY_CATL = "CATL"
