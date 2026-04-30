class TextRefineError(Exception):
    """Base exception for TextRefineAI."""


class InputError(TextRefineError):
    """Raised when user input cannot be processed."""


class ProviderConfigurationError(TextRefineError):
    """Raised when a model provider is missing required configuration."""


class ProviderResponseError(TextRefineError):
    """Raised when a model provider returns an unusable response."""
