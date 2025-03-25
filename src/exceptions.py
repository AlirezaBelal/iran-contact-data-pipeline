"""Custom exceptions for the contact cleaner application."""


class ContactCleanerError(Exception):
    """Base exception for contact cleaner errors."""
    pass


class FileProcessingError(ContactCleanerError):
    """Raised when there's an error processing input or output files."""
    pass


class ContactNormalizationError(ContactCleanerError):
    """Raised when phone number normalization fails."""
    pass
