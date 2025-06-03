"""
Prosty skrypt testujący działanie ThreadManager.
"""

import time

from utils.improved_thread_manager import ThreadManager


def test_func():
    """Prosta funkcja testowa"""
    time.sleep(0.5)
    print("Zadanie wykonane!")
    return "test result"


def main():
    """Funkcja główna testu"""
    manager = ThreadManager(enable_logging=False)
    print("Inicjalizacja zakończona")

    task_id = manager.submit_task(test_func)
    print(f"Task submitted: {task_id}")

    # Poczekaj na zakończenie
    time.sleep(1)

    # Sprawdź metryki
    metrics = manager.get_performance_metrics()
    print(f"Metryki: {metrics}")

    # Sprawdź stan zdrowia
    health = manager.get_thread_health_status()
    print(f"Stan zdrowia: {health}")

    # Czyszczenie
    manager.cleanup()
    print("Cleanup zakończony")


if __name__ == "__main__":
    main()
