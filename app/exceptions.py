"""Exceptions module for the TrailBlazeApp-Scrapers project."""


class ScraperException(Exception):
    """Base exception class for all scraper-related exceptions."""


class HTMLDownloadError(ScraperException):
    """Exception raised when HTML content cannot be downloaded from a URL."""


class DataExtractionError(ScraperException):
    """Exception raised when data cannot be extracted from HTML content."""


class DatabaseError(ScraperException):
    """Exception raised when a database operation fails."""


class CacheError(ScraperException):
    """Exception raised when a cache operation fails."""


class ValidationError(ScraperException):
    """Exception raised when data validation fails."""


class LLMAPIError(ScraperException):
    """Custom exception for LLM API request errors (connection, timeout, status codes)."""


class LLMContentError(ScraperException):
    """Custom exception for errors related to LLM response content (e.g., moderation flags, unexpected format)."""


class LLMJsonParsingError(ScraperException):
    """Custom exception for errors parsing JSON from the LLM response."""
