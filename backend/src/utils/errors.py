class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


class UpstreamError(Exception):
    """Raised when an upstream service (LLM) fails in a recoverable way."""
