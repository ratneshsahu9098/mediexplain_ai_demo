"""Pipeline-specific exceptions."""


class ProcessingError(Exception):
    """Raised when a document cannot be processed into usable text."""


class OcrUnavailableError(ProcessingError):
    """Raised when OCR is required but Tesseract is not installed."""
