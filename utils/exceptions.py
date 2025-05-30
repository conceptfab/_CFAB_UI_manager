# Custom Exception Classes
# Strukturyzowane wyjątki dla lepszej obsługi błędów

import logging

logger = logging.getLogger(__name__)


class CFABError(Exception):
    """
    Bazowa klasa dla wszystkich wyjątków w aplikacji CFAB
    """

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "CFAB_UNKNOWN"
        self.details = details or {}

        # Automatyczne logowanie błędu
        logger.error(f"[{self.error_code}] {message}", extra={"details": self.details})


class ConfigurationError(CFABError):
    """
    Błędy związane z konfiguracją aplikacji
    """

    def __init__(self, message: str, config_path: str = None, **kwargs):
        super().__init__(message, "CFAB_CONFIG", **kwargs)
        self.config_path = config_path


class HardwareProfilingError(CFABError):
    """
    Błędy związane z profilowaniem sprzętu
    """

    def __init__(self, message: str, hardware_type: str = None, **kwargs):
        super().__init__(message, "CFAB_HARDWARE", **kwargs)
        self.hardware_type = hardware_type


class ThreadManagementError(CFABError):
    """
    Błędy związane z zarządzaniem wątkami
    """

    def __init__(self, message: str, thread_id: str = None, **kwargs):
        super().__init__(message, "CFAB_THREAD", **kwargs)
        self.thread_id = thread_id


class TranslationError(CFABError):
    """
    Błędy związane z tłumaczeniami
    """

    def __init__(self, message: str, language: str = None, key: str = None, **kwargs):
        super().__init__(message, "CFAB_TRANSLATION", **kwargs)
        self.language = language
        self.key = key


class FileOperationError(CFABError):
    """
    Błędy związane z operacjami na plikach
    """

    def __init__(
        self, message: str, file_path: str = None, operation: str = None, **kwargs
    ):
        super().__init__(message, "CFAB_FILE", **kwargs)
        self.file_path = file_path
        self.operation = operation


class UIError(CFABError):
    """
    Błędy związane z interfejsem użytkownika
    """

    def __init__(self, message: str, widget_name: str = None, **kwargs):
        super().__init__(message, "CFAB_UI", **kwargs)
        self.widget_name = widget_name


class PerformanceError(CFABError):
    """
    Błędy związane z optymalizacją wydajności
    """

    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, "CFAB_PERFORMANCE", **kwargs)
        self.operation = operation


class ValidationError(CFABError):
    """
    Błędy związane z walidacją danych
    """

    def __init__(self, message: str, field: str = None, value: str = None, **kwargs):
        super().__init__(message, "CFAB_VALIDATION", **kwargs)
        self.field = field
        self.value = value


class CacheError(CFABError):
    """
    Błędy związane z systemem cache'owania
    """

    def __init__(self, message: str, cache_key: str = None, **kwargs):
        super().__init__(message, "CFAB_CACHE", **kwargs)
        self.cache_key = cache_key


# Funkcje pomocnicze do obsługi błędów


def handle_error_gracefully(func):
    """
    Dekorator do graceful error handling
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CFABError as e:
            # CFAB errors są już zalogowane
            raise
        except Exception as e:
            # Wrap nieznane błędy w CFABError
            logger.exception(f"Unexpected error in {func.__name__}")
            raise CFABError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                "CFAB_UNEXPECTED",
                {"original_error": str(e), "function": func.__name__},
            )

    return wrapper


def log_error_with_context(error: Exception, context: dict = None):
    """
    Loguje błąd z dodatkowym kontekstem
    """
    context = context or {}
    if isinstance(error, CFABError):
        logger.error(
            f"[{error.error_code}] {error.message}",
            extra={"details": error.details, "context": context},
        )
    else:
        logger.error(
            f"Unhandled error: {str(error)}", extra={"context": context}, exc_info=True
        )
