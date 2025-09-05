# Author: Jaime Yan
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(log_dir: str = "logs") -> None:
    """Setup logging with proper Unicode support and file rotation"""
    try:
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"app_{timestamp}.log")
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        ))
        
        # File handler with UTF-8 encoding and rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        ))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Add new handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Set encoding for stdout/stderr
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
            
        logging.info("Logging system initialized with Unicode support")
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}", file=sys.stderr)
        raise

def get_logger(name: str) -> logging.Logger:
    """Get a logger with proper Unicode support"""
    return logging.getLogger(name) 