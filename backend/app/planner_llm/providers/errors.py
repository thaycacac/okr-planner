class ProviderError(Exception):
    """Base error raised by LLM adapters.

    Messages must never contain prompt or OKR content: they end up in traces and logs.
    """


class ProviderUnavailableError(ProviderError):
    """Transport, auth, config or server failure; resending the same prompt will not help."""


class ProviderTimeoutError(ProviderUnavailableError):
    """The pipeline still retries a local timeout once; a warm model often finishes."""


class ProviderConnectionError(ProviderUnavailableError):
    pass


class ProviderAuthError(ProviderUnavailableError):
    pass


class ProviderNotConfiguredError(ProviderUnavailableError):
    pass


class ModelNotFoundError(ProviderUnavailableError):
    pass


class InvalidJSONError(ProviderError):
    """The model answered but the content is not a JSON object; worth a retry with feedback."""
