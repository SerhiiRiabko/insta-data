"""Custom exception classes"""


class InstaDataException(Exception):
    """Base exception for Insta-data"""
    pass


class DatabaseException(InstaDataException):
    """Database connection error"""
    pass


class ScraperException(InstaDataException):
    """Scraper error"""
    pass


class ValidationException(InstaDataException):
    """Data validation error"""
    pass