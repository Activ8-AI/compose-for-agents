"""
Domain-specific exceptions for the Teamwork pipeline.
"""


class PipelineError(RuntimeError):
    """Base class for pipeline failures."""


class ClientNotFoundError(PipelineError):
    """Raised when the client matrix cannot resolve a client_id."""


class InvalidExecutionIntentError(PipelineError):
    """Raised when the incoming intent payload fails validation."""
