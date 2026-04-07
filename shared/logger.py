"""
Logging configuration for Battery Analysis System
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from config.settings import config


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance"""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, config.log_level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.log_level))
    
    # File handler
    log_dir = Path(config.output_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"battery_analysis_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
