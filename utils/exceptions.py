# Custom Exception Classes
# Strukturyzowane wyjątki dla lepszej obsługi błędów

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

    # Szczegółowe kody błędów
    CONFIG_NOT_FOUND = "CFAB_CONFIG_NOT_FOUND"
    CONFIG_INVALID_FORMAT = "CFAB_CONFIG_INVALID_FORMAT"
    CONFIG_MISSING_REQUIRED = "CFAB_CONFIG_MISSING_REQUIRED"

    FILE_NOT_FOUND = "CFAB_FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "CFAB_FILE_ACCESS_DENIED"
    FILE_CORRUPT = "CFAB_FILE_CORRUPT"

    HARDWARE_DRIVER_MISSING = "CFAB_HARDWARE_DRIVER_MISSING"
    HARDWARE_INSUFFICIENT = "CFAB_HARDWARE_INSUFFICIENT"
    HARDWARE_INCOMPATIBLE = "CFAB_HARDWARE_INCOMPATIBLE"

    THREAD_TIMEOUT = "CFAB_THREAD_TIMEOUT"
    THREAD_INTERRUPT = "CFAB_THREAD_INTERRUPT"

    UI_RENDER_ERROR = "CFAB_UI_RENDER_ERROR"
    UI_EVENT_ERROR = "CFAB_UI_EVENT_ERROR"

    NETWORK_CONNECTION_ERROR = "CFAB_NETWORK_CONNECTION_ERROR"
    NETWORK_TIMEOUT = "CFAB_NETWORK_TIMEOUT"

    API_ERROR = "CFAB_API_ERROR"
    API_RESPONSE_INVALID = "CFAB_API_RESPONSE_INVALID"

    RESOURCE_UNAVAILABLE = "CFAB_RESOURCE_UNAVAILABLE"
    RESOURCE_EXHAUSTED = "CFAB_RESOURCE_EXHAUSTED"

    SECURITY_ERROR = "CFAB_SECURITY_ERROR"
    SECURITY_PERMISSION_DENIED = "CFAB_SECURITY_PERMISSION_DENIED"

    DATABASE_ERROR = "CFAB_DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "CFAB_DATABASE_CONNECTION_ERROR"


class CFABError(Exception):
    """
    Bazowa klasa dla wszystkich wyjątków w aplikacji CFAB.
    Umożliwia dodanie kodu błędu i dodatkowych szczegółów.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN,
        details: dict = None,
        original_exception: Exception = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception

        # Add original exception type and message to details if present
        if original_exception:
            self.details["original_exception_type"] = type(original_exception).__name__
            self.details["original_exception_message"] = str(original_exception)

        # Automatyczne logowanie błędu
        logger.error(
            f"[{self.error_code.value}] {message}", extra={"details": self.details}
        )


# --- Specific Error Classes (Simplified) ---
# Można teraz używać CFABError bezpośrednio z odpowiednim ErrorCode,
# lub tworzyć bardziej szczegółowe klasy, jeśli potrzebują dodatkowej logiki/pól.


# Przykład: Jeśli ConfigurationError potrzebuje specjalnego pola config_path
class ConfigurationError(CFABError):
    """
    Błędy związane z konfiguracją aplikacji.

    Przykłady zastosowania:
    - Brak pliku konfiguracyjnego
    - Nieprawidłowy format pliku konfiguracyjnego
    - Brakujące wymagane pola konfiguracji
    """

    def __init__(
        self,
        message: str,
        config_path: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.CONFIG,
    ):
        details = details or {}
        if config_path:
            details["config_path"] = config_path
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.config_path = config_path


# Dla pozostałych, jeśli nie ma dodatkowych pól, można używać CFABError bezpośrednio:
# raise CFABError("Błąd profilowania sprzętu", ErrorCode.HARDWARE, details={"type": "GPU"})


# Jeśli jednak chcemy zachować dedykowane klasy dla czytelności lub przyszłej rozbudowy:
class HardwareProfilingError(CFABError):
    """
    Błędy związane z profilowaniem sprzętu.

    Przykłady zastosowania:
    - Brak sterowników urządzenia
    - Niewystarczające zasoby sprzętowe
    - Niekompatybilny sprzęt
    """

    def __init__(
        self,
        message: str,
        hardware_type: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.HARDWARE,
    ):
        details = details or {}
        if hardware_type:
            details["hardware_type"] = hardware_type
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.hardware_type = hardware_type


class ThreadManagementError(CFABError):
    """
    Błędy związane z zarządzaniem wątkami.

    Przykłady zastosowania:
    - Timeout wątku
    - Przerwanie wątku
    - Błąd synchronizacji
    """

    def __init__(
        self,
        message: str,
        thread_id: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.THREAD,
    ):
        details = details or {}
        if thread_id:
            details["thread_id"] = thread_id
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.thread_id = thread_id


class TranslationError(CFABError):
    """
    Błędy związane z tłumaczeniami.

    Przykłady zastosowania:
    - Brak klucza tłumaczenia
    - Nieprawidłowy format pliku tłumaczeń
    - Nieobsługiwany język
    """

    def __init__(
        self,
        message: str,
        language: str = None,
        key: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.TRANSLATION,
    ):
        details = details or {}
        if language:
            details["language"] = language
        if key:
            details["key"] = key
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.language = language
        self.key = key


class FileOperationError(CFABError):
    """
    Błędy związane z operacjami na plikach.

    Przykłady zastosowania:
    - Plik nie istnieje
    - Brak uprawnień dostępu
    - Plik uszkodzony lub nieprawidłowy format
    """

    def __init__(
        self,
        message: str,
        file_path: str = None,
        operation: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.FILE,
    ):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        if operation:
            details["operation"] = operation
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.file_path = file_path
        self.operation = operation


class UIError(CFABError):
    """
    Błędy związane z interfejsem użytkownika.

    Przykłady zastosowania:
    - Błąd renderowania komponentu
    - Nieprawidłowa obsługa zdarzenia
    - Niekompatybilność komponentów UI
    """

    def __init__(
        self,
        message: str,
        widget_name: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.UI,
    ):
        details = details or {}
        if widget_name:
            details["widget_name"] = widget_name
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.widget_name = widget_name


class PerformanceError(CFABError):
    """
    Błędy związane z optymalizacją wydajności.

    Przykłady zastosowania:
    - Operacja trwa zbyt długo (timeout)
    - Wysoki poziom zużycia zasobów
    - Problemy z wydajnością renderowania
    """

    def __init__(
        self,
        message: str,
        operation: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.PERFORMANCE,
    ):
        details = details or {}
        if operation:
            details["operation"] = operation
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.operation = operation


class ValidationError(CFABError):
    """
    Błędy związane z walidacją danych.

    Przykłady zastosowania:
    - Nieprawidłowy format danych
    - Wartość poza dopuszczalnym zakresem
    - Brak wymaganych danych
    """

    def __init__(
        self,
        message: str,
        field: str = None,
        value: any = None,  # Zmieniono typ na 'any' dla większej elastyczności
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.VALIDATION,
    ):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:  # Sprawdzamy czy value nie jest None
            details["value"] = value
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.field = field
        self.value = value


class CacheError(CFABError):
    """
    Błędy związane z systemem cache'owania.

    Przykłady zastosowania:
    - Brak klucza w cache
    - Nieaktualne dane w cache
    - Problemy z zapisem do cache
    """

    def __init__(
        self,
        message: str,
        cache_key: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.CACHE,
    ):
        details = details or {}
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.cache_key = cache_key


# Nowe klasy wyjątków domenowych


class NetworkError(CFABError):
    """
    Błędy związane z operacjami sieciowymi.

    Przykłady zastosowania:
    - Brak połączenia sieciowego
    - Timeout połączenia
    - Problemy z DNS
    """

    def __init__(
        self,
        message: str,
        url: str = None,
        status_code: int = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.NETWORK_CONNECTION_ERROR,
    ):
        details = details or {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.url = url
        self.status_code = status_code


class APIError(CFABError):
    """
    Błędy związane z komunikacją z API.

    Przykłady zastosowania:
    - Nieprawidłowa odpowiedź API
    - Błąd autoryzacji API
    - Nieoczekiwany format odpowiedzi
    """

    def __init__(
        self,
        message: str,
        endpoint: str = None,
        method: str = None,
        response_code: int = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.API_ERROR,
    ):
        details = details or {}
        if endpoint:
            details["endpoint"] = endpoint
        if method:
            details["method"] = method
        if response_code:
            details["response_code"] = response_code
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.endpoint = endpoint
        self.method = method
        self.response_code = response_code


class ResourceError(CFABError):
    """
    Błędy związane z zasobami systemowymi.

    Przykłady zastosowania:
    - Brak dostępu do zasobu
    - Wyczerpanie zasobów (pamięć, dysk)
    - Konflikt dostępu do zasobu
    """

    def __init__(
        self,
        message: str,
        resource_type: str = None,
        resource_id: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.RESOURCE_UNAVAILABLE,
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class SecurityError(CFABError):
    """
    Błędy związane z bezpieczeństwem.

    Przykłady zastosowania:
    - Brak uprawnień
    - Nieautoryzowany dostęp
    - Podejrzana aktywność
    """

    def __init__(
        self,
        message: str,
        security_context: str = None,
        user_id: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.SECURITY_ERROR,
    ):
        details = details or {}
        if security_context:
            details["security_context"] = security_context
        if user_id:
            details["user_id"] = user_id
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.security_context = security_context
        self.user_id = user_id


class DatabaseError(CFABError):
    """
    Błędy związane z operacjami bazodanowymi.

    Przykłady zastosowania:
    - Błąd połączenia z bazą danych
    - Błąd zapytania SQL
    - Naruszenie integralności danych
    """

    def __init__(
        self,
        message: str,
        query: str = None,
        table: str = None,
        details: dict = None,
        original_exception: Exception = None,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
    ):
        details = details or {}
        if query:
            # For security, we might want to sanitize SQL queries in logs
            sanitized_query = query[:100] + "..." if len(query) > 100 else query
            details["query"] = sanitized_query
        if table:
            details["table"] = table
        super().__init__(
            message,
            error_code,
            details=details,
            original_exception=original_exception,
        )
        self.query = query
        self.table = table


# Funkcje pomocnicze do obsługi błędów


def handle_error_gracefully(func):
    """
    Dekorator do graceful error handling.
    Loguje błędy CFABError i opakowuje nieoczekiwane wyjątki w CFABError.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CFABError:
            # CFAB errors są już zalogowane przez __init__ CFABError
            raise
        except Exception as e:
            # Wrap nieznane błędy w CFABError
            logger.exception(f"Unexpected error in {func.__name__}")
            raise CFABError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                ErrorCode.UNEXPECTED,
                details={"function_name": func.__name__},
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


# Dodatkowe funkcje pomocnicze do obsługi błędów


def try_except_with_context(context=None):
    """
    Dekorator kontekstowy do obsługi i logowania wyjątków.
    Automatycznie dodaje kontekst do logowania błędów.

    Przykład użycia:
    @try_except_with_context({"component": "UserService"})
    def get_user_data(user_id):
        # kod funkcji
    """
    context = context or {}

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CFABError as e:
                # Dodaj kontekst do istniejącego błędu CFAB
                log_error_with_context(e, {**context, "function": func.__name__})
                raise
            except Exception as e:
                # Opakuj nieznany wyjątek w CFABError z kontekstem
                logger.exception(f"Error in {func.__name__}")
                wrapped_error = CFABError(
                    f"Error in {func.__name__}: {str(e)}",
                    ErrorCode.UNEXPECTED,
                    details={"function": func.__name__, **context},
                    original_exception=e,
                )
                raise wrapped_error

        return wrapper

    return decorator


def safe_operation(default_value=None, error_code=ErrorCode.UNEXPECTED):
    """
    Dekorator do bezpiecznego wykonywania operacji z wartością domyślną w razie błędu.

    Przykład użycia:
    @safe_operation(default_value=[], error_code=ErrorCode.FILE)
    def read_file_lines(file_path):
        with open(file_path) as f:
            return f.readlines()
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error but don't raise
                logger.error(
                    f"Error in {func.__name__}, returning default value: {default_value}",
                    extra={
                        "error_code": error_code.value,
                        "args": args,
                        "kwargs": {
                            k: v
                            for k, v in kwargs.items()
                            if not k.startswith("password")
                        },
                        "default_value": default_value,
                        "exception": str(e),
                    },
                    exc_info=True,
                )
                return default_value

        return wrapper

    return decorator
