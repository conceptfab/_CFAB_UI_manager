# Custom Exception Classes
# Strukturyzowane wyjątki dla lepszej obsługi błędów

import functools  # Dodany import
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Enum for error codes to ensure consistency."""

    UNKNOWN = "CFAB_UNKNOWN"
    CONFIG = "CFAB_CONFIG"
    HARDWARE = "CFAB_HARDWARE"
    THREAD = "CFAB_THREAD"
    TRANSLATION = "CFAB_TRANSLATION"
    FILE = "CFAB_FILE"
    UI = "CFAB_UI"
    PERFORMANCE = "CFAB_PERFORMANCE"
    VALIDATION = "CFAB_VALIDATION"
    CACHE = "CFAB_CACHE"
    UNEXPECTED = "CFAB_UNEXPECTED"
    # Add more specific error codes as needed, e.g.:
    # FILE_NOT_FOUND = "CFAB_FILE_NOT_FOUND"
    # NETWORK_ERROR = "CFAB_NETWORK_ERROR"


class CFABError(Exception):
    """
    Bazowa klasa dla wszystkich wyjątków w aplikacji CFAB.
    """

    def __init__(self, message, error_code=None, **context):
        self.message = message
        self.error_code = error_code or ErrorCode.UNKNOWN
        self.context = context
        super().__init__(message)

        # Automatyczne logowanie błędów
        logger.error(f"{self.error_code.value}: {message}", extra={"context": context})


# --- Specific Error Classes (Simplified) ---
# Można teraz używać CFABError bezpośrednio z odpowiednim ErrorCode,
# lub tworzyć bardziej szczegółowe klasy, jeśli potrzebują dodatkowej logiki/pól.


# Przykład: Jeśli ConfigurationError potrzebuje specjalnego pola config_path
class ConfigurationError(CFABError):
    """Błędy związane z konfiguracją aplikacji."""

    def __init__(
        self,
        message: str,
        config_path: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if config_path:
            details["config_path"] = config_path
        super().__init__(
            message,
            ErrorCode.CONFIG,
            details=details,
            original_exception=original_exception,
        )
        self.config_path = config_path


# Dla pozostałych, jeśli nie ma dodatkowych pól, można używać CFABError bezpośrednio:
# raise CFABError("Błąd profilowania sprzętu", ErrorCode.HARDWARE, details={"type": "GPU"})


# Jeśli jednak chcemy zachować dedykowane klasy dla czytelności lub przyszłej rozbudowy:
class HardwareProfilingError(CFABError):
    """Błędy związane z profilowaniem sprzętu."""

    def __init__(
        self,
        message: str,
        hardware_type: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if hardware_type:
            details["hardware_type"] = hardware_type
        super().__init__(
            message,
            ErrorCode.HARDWARE,
            details=details,
            original_exception=original_exception,
        )
        self.hardware_type = hardware_type


class ThreadManagementError(CFABError):
    """Błędy związane z zarządzaniem wątkami."""

    def __init__(
        self,
        message: str,
        thread_id: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if thread_id:
            details["thread_id"] = thread_id
        super().__init__(
            message,
            ErrorCode.THREAD,
            details=details,
            original_exception=original_exception,
        )
        self.thread_id = thread_id


class TranslationError(CFABError):
    """Błędy związane z tłumaczeniami."""

    def __init__(
        self,
        message: str,
        language: str = None,
        key: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if language:
            details["language"] = language
        if key:
            details["key"] = key
        super().__init__(
            message,
            ErrorCode.TRANSLATION,
            details=details,
            original_exception=original_exception,
        )
        self.language = language
        self.key = key


class FileOperationError(CFABError):
    """Błędy związane z operacjami na plikach."""

    def __init__(
        self,
        message: str,
        file_path: str = None,
        operation: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        super().__init__(
            message,
            ErrorCode.FILE,
            details=details,
            original_exception=original_exception,
        )
        self.file_path = file_path
        self.operation = operation


class UIError(CFABError):
    """Błędy związane z interfejsem użytkownika."""

    def __init__(
        self,
        message: str,
        widget_name: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if widget_name:
            details["widget_name"] = widget_name
        super().__init__(
            message,
            ErrorCode.UI,
            details=details,
            original_exception=original_exception,
        )
        self.widget_name = widget_name


class PerformanceError(CFABError):
    """Błędy związane z optymalizacją wydajności."""

    def __init__(
        self,
        message: str,
        operation: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if operation:
            details["operation"] = operation
        super().__init__(
            message,
            ErrorCode.PERFORMANCE,
            details=details,
            original_exception=original_exception,
        )
        self.operation = operation


class ValidationError(CFABError):
    """Błędy związane z walidacją danych."""

    def __init__(
        self,
        message: str,
        field: str = None,
        value: any = None,  # Zmieniono typ na 'any' dla większej elastyczności
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:  # Sprawdzamy czy value nie jest None
            details["value"] = value
        super().__init__(
            message,
            ErrorCode.VALIDATION,
            details=details,
            original_exception=original_exception,
        )
        self.field = field
        self.value = value


class CacheError(CFABError):
    """Błędy związane z systemem cache\'owania."""

    def __init__(
        self,
        message: str,
        cache_key: str = None,
        details: dict = None,
        original_exception: Exception = None,
    ):
        details = details or {}
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(
            message,
            ErrorCode.CACHE,
            details=details,
            original_exception=original_exception,
        )
        self.cache_key = cache_key


# Funkcje pomocnicze do obsługi błędów


def handle_error_gracefully(func):
    """
    Dekorator do graceful error handling.
    Loguje błędy CFABError i opakowuje nieoczekiwane wyjątki w CFABError.
    """

    @functools.wraps(func)  # Dodanie @functools.wraps
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CFABError:
            # CFAB errors są już zalogowane przez __init__ CFABError
            raise
        except Exception as e:
            # Wrap nieznane błędy w CFABError
            logger.exception(
                f"Unexpected error in {func.__name__}"
            )  # Użycie logger.exception
            raise CFABError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                ErrorCode.UNEXPECTED,
                context={"function_name": func.__name__},  # Zmiana details na context
                original_exception=e,
            )

    return wrapper


def log_error_with_context(error: Exception, context: dict = None):
    """
    Loguje błąd z dodatkowym kontekstem.
    Jeśli błąd nie jest instancją CFABError, jest logowany jako nieobsłużony.
    """
    context = context or {}
    if isinstance(error, CFABError):
        # CFABError loguje się sam przy inicjalizacji,
        # ale możemy dodać dodatkowy kontekst, jeśli jest potrzebny.
        # Tworzymy kopię details, aby nie modyfikować oryginalnego obiektu błędu.
        log_details = {**error.details, "additional_context": context}
        logger.error(
            f"[{error.error_code.value}] {error.message} (Contextual Log)",
            extra={"details": log_details},
        )
    else:
        logger.error(
            f"Unhandled error: {str(error)} (Contextual Log)",
            extra={"context": context, "original_exception_type": type(error).__name__},
            exc_info=True,  # Dołącza traceback dla nie-CFAB błędów
        )
