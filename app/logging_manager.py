"""Logging manager module for the TrailBlazeApp-Scrapers project."""

import logging
import sys
from typing import Optional
from colorama import Fore, Style, init

# Import emoji with error handling
try:
    from emoji import emojize
except ImportError:
    # Fallback if emoji module is not installed
    def emojize(text, **kwargs):
        return text

# Initialize colorama
init(autoreset=True)


class LoggingManager:
    """
    Manages logging configuration and provides utility methods for formatted logging.
    
    Configures the Python logging module with appropriate formatters and handlers.
    Provides methods for color-coded and emoji-enhanced logging at various levels.
    """

    def __init__(self, logger_name: str, level: int = logging.INFO) -> None:
        """
        Initialize the LoggingManager with a named logger.
        
        Args:
            logger_name (str): Name for the logger, typically __name__ of the calling module
            level (int): Logging level (default: logging.INFO)
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        
        # Only add handler if logger doesn't already have handlers
        if not self.logger.handlers:
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, emoji: Optional[str] = None) -> None:
        """
        Log a debug message, optionally with an emoji.
        
        Args:
            message (str): The message to log
            emoji (Optional[str]): Emoji shortcode to prepend to the message
        """
        formatted_message = self._format_message(message, emoji, Fore.CYAN)
        self.logger.debug(formatted_message)
    
    def info(self, message: str, emoji: Optional[str] = None) -> None:
        """
        Log an info message, optionally with an emoji.
        
        Args:
            message (str): The message to log
            emoji (Optional[str]): Emoji shortcode to prepend to the message
        """
        formatted_message = self._format_message(message, emoji, Fore.GREEN)
        self.logger.info(formatted_message)
    
    def warning(self, message: str, emoji: Optional[str] = None) -> None:
        """
        Log a warning message, optionally with an emoji.
        
        Args:
            message (str): The message to log
            emoji (Optional[str]): Emoji shortcode to prepend to the message
        """
        formatted_message = self._format_message(message, emoji, Fore.YELLOW)
        self.logger.warning(formatted_message)
    
    def error(self, message: str, emoji: Optional[str] = None) -> None:
        """
        Log an error message, optionally with an emoji.
        
        Args:
            message (str): The message to log
            emoji (Optional[str]): Emoji shortcode to prepend to the message
        """
        formatted_message = self._format_message(message, emoji, Fore.RED)
        self.logger.error(formatted_message)
    
    def critical(self, message: str, emoji: Optional[str] = None) -> None:
        """
        Log a critical message, optionally with an emoji.
        
        Args:
            message (str): The message to log
            emoji (Optional[str]): Emoji shortcode to prepend to the message
        """
        formatted_message = self._format_message(
            message, 
            emoji or ":skull:", 
            Fore.RED + Style.BRIGHT
        )
        self.logger.critical(formatted_message)
    
    def _format_message(self, message: str, emoji: Optional[str], color: str) -> str:
        """
        Format a log message with optional emoji and color.
        
        Args:
            message (str): The message to format
            emoji (Optional[str]): Emoji shortcode to prepend to the message
            color (str): ANSI color code to apply to the message
        
        Returns:
            str: Formatted message
        """
        if emoji:
            return f"{emojize(emoji, language='alias')} {color}{message}{Style.RESET_ALL}"
        return f"{color}{message}{Style.RESET_ALL}"


def get_logger(name: str, level: int = logging.INFO) -> LoggingManager:
    """
    Factory function to create and return a LoggingManager instance.
    
    Args:
        name (str): Name for the logger, typically __name__ of the calling module
        level (int): Logging level (default: logging.INFO)
    
    Returns:
        LoggingManager: Configured logging manager instance
    """
    return LoggingManager(name, level)
