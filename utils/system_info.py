"""
Moduł zawierający funkcje związane z identyfikacją i informacjami o systemie.

Ten moduł udostępnia funkcje do identyfikacji sprzętu, generowania stabilnych UUID
oraz innych operacji związanych z informacjami systemowymi.
"""

import logging
import platform
import re
import uuid
from functools import lru_cache

from utils.secure_commands import (
    CommandExecutionError,
    CommandTimeoutError,
    SecureCommandRunner,
)

logger = logging.getLogger(__name__)

# Cache dla UUID - globalny dla całej aplikacji
_UUID_CACHE = None


@lru_cache(maxsize=1)
def get_stable_uuid():
    """
    Generuje stabilny identyfikator UUID oparty na stałych parametrach sprzętowych.

    Ta funkcja wykorzystuje lru_cache do przechowywania wyniku w pamięci podręcznej,
    więc kolejne wywołania będą zwracać tę samą wartość UUID bez ponownego obliczania.

    Returns:
        str: Stabilny identyfikator UUID dla obecnej maszyny
    """
    global _UUID_CACHE

    # Jeśli UUID jest już w cache globalnym, zwróć go
    if _UUID_CACHE is not None:
        logger.debug("Returning cached UUID from global cache")
        return _UUID_CACHE

    machine_id_str = ""
    secure_runner = SecureCommandRunner()

    # Try to get a unique machine identifier
    if platform.system() == "Windows":
        try:
            # Motherboard serial number is often a good candidate
            stdout, _ = secure_runner.run_command(
                ["wmic", "baseboard", "get", "serialnumber"], timeout=10
            )
            lines = stdout.split("\n")
            if len(lines) > 1:
                serial = lines[1].strip()
                if serial and serial != "To be filled by O.E.M.":
                    machine_id_str = serial
                    logger.debug(f"Got Windows motherboard serial: {serial}")
        except (CommandTimeoutError, CommandExecutionError):
            logger.debug("Failed to get Windows motherboard serial")

    elif platform.system() == "Linux":
        try:
            # /etc/machine-id is usually available and stable
            with open("/etc/machine-id", "r") as f:
                machine_id_str = f.read().strip()
                logger.debug(f"Got Linux machine-id: {machine_id_str}")
        except FileNotFoundError:
            logger.debug("Failed to read /etc/machine-id")

    elif platform.system() == "Darwin":  # macOS
        try:
            # IOPlatformUUID is a good candidate on macOS
            stdout, _ = secure_runner.run_command(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"], timeout=10
            )
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', stdout)
            if match:
                machine_id_str = match.group(1)
                logger.debug(f"Got macOS IOPlatformUUID: {machine_id_str}")
        except (CommandTimeoutError, CommandExecutionError):
            logger.debug("Failed to get macOS IOPlatformUUID")

    # Fallback if specific IDs aren't available or if they are empty
    if not machine_id_str:
        machine_id_str = (
            platform.node()
            + platform.machine()
            + (platform.processor() or "unknown_processor")
        )
        logger.debug(f"Using fallback machine ID: {machine_id_str}")

    # Generujemy UUID i zapisujemy go w globalnym cache
    result_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, machine_id_str))
    _UUID_CACHE = result_uuid
    logger.debug(f"Generated stable UUID: {result_uuid}")

    return result_uuid


def clear_uuid_cache():
    """
    Czyści cache UUID. Przydatne w testach lub kiedy chcemy wymusić ponowne wygenerowanie UUID.
    """
    global _UUID_CACHE
    get_stable_uuid.cache_clear()  # Czyści cache funkcji z dekoratora lru_cache
    _UUID_CACHE = None
    logger.debug("UUID cache cleared")


def get_system_info():
    """
    Zwraca słownik z podstawowymi informacjami o systemie.

    Returns:
        dict: Informacje o systemie
    """
    return {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
