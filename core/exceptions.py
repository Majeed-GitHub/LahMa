"""
Custom exceptions for the LahMa application.
Provides specific error types for different parts of the application.
"""


class LahMaError(Exception):
    """Base exception for all LahMa application errors."""

    def __init__(self, message="An unspecified LahMa error occurred."):
        super().__init__(message)


class ConfigError(LahMaError):
    """Errors related to loading, parsing, or validating configuration."""

    def __init__(self, message="Configuration error."):
        super().__init__(message)


class EnvironmentError(LahMaError):
    """Errors related to the runtime environment (e.g., missing dependencies)."""

    def __init__(self, message="Environment error."):
        super().__init__(message)


class ModuleError(LahMaError):
    """Base class for module-specific errors."""

    def __init__(
        self, module_name: str, message: str = "An error occurred in the module."
    ):
        self.module_name = module_name
        full_message = f"[{module_name} Module Error]: {message}"
        super().__init__(full_message)


class HoneypotError(ModuleError):
    """Honeypot module specific errors."""

    def __init__(self, message: str = "Honeypot operation failed."):
        super().__init__(module_name="Honeypot", message=message)


class EsxiTesterError(ModuleError):
    """ESXi Tester module specific errors."""

    def __init__(self, message: str = "ESXi testing operation failed."):
        super().__init__(module_name="ESXi Tester", message=message)


class WebFuzzerError(ModuleError):
    """Web Fuzzer module specific errors."""

    def __init__(self, message: str = "Web Fuzzing operation failed."):
        super().__init__(module_name="Web Fuzzer", message=message)


class ApiError(LahMaError):
    """Errors related to interacting with external APIs (e.g., OpenAI)."""

    def __init__(
        self, service_name: str, message: str = "External API interaction failed."
    ):
        self.service_name = service_name
        full_message = f"[{service_name} API Error]: {message}"
        super().__init__(full_message)


# Example of how to raise:
# raise ConfigError("Missing 'openai_api_key' in configuration.")
# raise WebFuzzerError("Nuclei executable not found.")
# raise ApiError("OpenAI", "Rate limit exceeded.")
