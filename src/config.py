"""Configuration settings for the AI Data Matching Tool."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
# In production/Docker, this will be passed as environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"

# Validate OpenAI API key is available
if not OPENAI_API_KEY:
    import logging
    logging.warning("OPENAI_API_KEY not found in environment variables. LLM features may not work.")
    logging.warning("For Docker deployment, pass the key as: -e OPENAI_API_KEY='your-key-here'")

# Currency API Configuration - Using exchangerate-api.com (free, no key required)
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
CURRENCY_BACKUP_URL = "https://api.exchangerate.host/latest?base=USD"
CURRENCY_CACHE_DURATION = 3600  # 1 hour in seconds

# Matching Configuration
EXACT_MATCH_THRESHOLD = 1.0
FUZZY_MATCH_THRESHOLD = 0.85  # Conservative threshold to avoid false matches
MIN_MATCH_LENGTH = 3  # Minimum company name length for matching

# UI Configuration
BRAND_COLORS = {
    "primary": "#006FCF",  # Bright Blue
    "primary_70": "#4C9ADD",  # 70% tint
    "primary_35": "#A6CDEE",  # 35% tint
    "secondary": "#00175A",  # Deep Blue
    "accent": "#23A8D1",  # Sky Blue
    "text": "#2D3748",
    "background": "#FFFFFF",
    "success": "#68D391",
    "warning": "#F6E05E",
    "error": "#FC8181"
}

# File Processing
MAX_FILE_SIZE_MB = 50
SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls']

# Export Configuration
HTML_TEMPLATE_PATH = "templates/report_template.html"
EXPORT_FORMATS = ['HTML', 'Excel']