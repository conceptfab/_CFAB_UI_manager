# Secure Command Utilities
# Bezpieczne narzędzia do wykonywania komend systemowych

import logging
import platform
import shlex
import subprocess
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class CommandTimeoutError(Exception):
    """Wyjątek rzucany gdy komenda przekroczy timeout"""

    pass


class CommandExecutionError(Exception):
    """Wyjątek rzucany gdy komenda zakończy się błędem"""

    pass


class SecureCommandRunner:
    """
    Bezpieczna klasa do wykonywania komend systemowych
    """

    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout

    def run_command(
        self, command_parts: List[str], timeout: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Bezpiecznie wykonuje komendę systemową

        Args:
            command_parts: Lista części komendy (bez shell=True)
            timeout: Timeout w sekundach

        Returns:
            Tuple[stdout, stderr]

        Raises:
            CommandTimeoutError: Gdy komenda przekroczy timeout
            CommandExecutionError: Gdy komenda zakończy się błędem
        """
        if timeout is None:
            timeout = self.default_timeout

        try:
            logger.debug(f"Executing command: {' '.join(command_parts)}")
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # Nie rzucamy wyjątku automatycznie
            )

            if result.returncode != 0:
                error_msg = (
                    f"Command failed with code {result.returncode}: {result.stderr}"
                )
                logger.error(error_msg)
                raise CommandExecutionError(error_msg)

            logger.debug(f"Command succeeded: {len(result.stdout)} chars output")
            return result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout}s"
            logger.error(error_msg)
            raise CommandTimeoutError(error_msg)
        except FileNotFoundError as e:
            error_msg = f"Command not found: {e}"
            logger.error(error_msg)
            raise CommandExecutionError(error_msg)


class HardwareDetector:
    """
    Bezpieczne narzędzia do wykrywania sprzętu
    """

    def __init__(self):
        self.cmd_runner = SecureCommandRunner()

    def get_gpu_info_windows(self) -> str:
        """
        Bezpiecznie wykrywa GPU na Windows
        """
        try:
            # Bezpieczna wersja WMIC
            command = [
                "wmic",
                "path",
                "win32_VideoController",
                "get",
                "name",
                "/format:csv",
            ]
            stdout, _ = self.cmd_runner.run_command(command, timeout=15)

            # Parsowanie CSV output
            lines = stdout.strip().split("\n")
            gpus = []
            for line in lines[1:]:  # Skip header
                parts = line.split(",")
                if len(parts) >= 2 and parts[1].strip():
                    gpu_name = parts[1].strip()
                    if gpu_name.lower() != "name":
                        gpus.append(gpu_name)

            return ", ".join(gpus) if gpus else "N/A"

        except (CommandTimeoutError, CommandExecutionError) as e:
            logger.warning(f"GPU detection failed: {e}")
            return "Error detecting GPU"

    def get_gpu_info_linux(self) -> str:
        """
        Bezpiecznie wykrywa GPU na Linux
        """
        gpu_info_list = []

        # Próba lspci
        try:
            command = ["lspci", "-v"]
            stdout, _ = self.cmd_runner.run_command(command, timeout=10)

            for line in stdout.splitlines():
                if "VGA compatible controller" in line:
                    # Wyciągnij nazwę GPU z linii
                    parts = line.split(":")
                    if len(parts) >= 3:
                        gpu_name = parts[2].strip()
                        gpu_info_list.append(gpu_name)

        except (CommandTimeoutError, CommandExecutionError):
            logger.debug("lspci failed, trying nvidia-smi")

        # Próba nvidia-smi jeśli lspci nie zadziałało
        if not gpu_info_list:
            try:
                command = [
                    "nvidia-smi",
                    "--query-gpu=gpu_name",
                    "--format=csv,noheader",
                ]
                stdout, _ = self.cmd_runner.run_command(command, timeout=10)

                nvidia_gpus = [
                    line.strip() for line in stdout.splitlines() if line.strip()
                ]
                if nvidia_gpus:
                    gpu_info_list = nvidia_gpus

            except (CommandTimeoutError, CommandExecutionError):
                logger.debug("nvidia-smi also failed")

        return ", ".join(gpu_info_list) if gpu_info_list else "N/A (Linux)"

    def get_gpu_info_macos(self) -> str:
        """
        Bezpiecznie wykrywa GPU na macOS
        """
        try:
            command = ["system_profiler", "SPDisplaysDataType", "-xml"]
            stdout, _ = self.cmd_runner.run_command(command, timeout=15)

            # Prosty parser dla XML output
            gpus = []
            lines = stdout.splitlines()
            for i, line in enumerate(lines):
                if "_name" in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("<string>") and next_line.endswith(
                        "</string>"
                    ):
                        gpu_name = next_line[8:-9]  # Remove <string> tags
                        gpus.append(gpu_name)

            return ", ".join(gpus) if gpus else "N/A (macOS)"

        except (CommandTimeoutError, CommandExecutionError) as e:
            logger.warning(f"macOS GPU detection failed: {e}")
            return "Error detecting GPU"

    def get_gpu_info(self) -> str:
        """
        Automatycznie wykrywa GPU w zależności od systemu operacyjnego
        """
        system = platform.system()

        if system == "Windows":
            return self.get_gpu_info_windows()
        elif system == "Linux":
            return self.get_gpu_info_linux()
        elif system == "Darwin":  # macOS
            return self.get_gpu_info_macos()
        else:
            return f"N/A (Unsupported OS: {system})"
