"""
Test benchmarku AI z wykorzystaniem CuPy dla sprawdzenia zgodności sprzętowej.
Ten skrypt pomaga zweryfikować czy:
1. CuPy jest poprawnie zainstalowany
2. Karta GPU jest dostępna i działa
3. Możliwe jest wykonanie obliczeń na GPU

Użycie:
python test_cupy_benchmark.py
"""

import logging
import platform
import sys
import time
import warnings

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CuPy_Tester")

# Ignorowanie ostrzeżeń z CuPy
warnings.filterwarnings("ignore", category=UserWarning, module="cupy")


def test_cupy_import():
    """Sprawdza, czy CuPy można zaimportować"""
    logger.info("Próba importu CuPy...")

    try:
        import cupy as cp

        logger.info("✅ CuPy zaimportowane pomyślnie!")
        return cp
    except ImportError as e:
        logger.error(f"❌ Nie udało się zaimportować CuPy: {e}")
        logger.info("Sprawdź czy biblioteka CuPy jest zainstalowana: pip install cupy")
        return None
    except Exception as e:
        logger.error(f"❌ Nieoczekiwany błąd podczas importu CuPy: {e}")
        return None


def get_system_info():
    """Wyświetla informacje o systemie"""
    logger.info("=== Informacje o systemie ===")
    logger.info(f"System: {platform.system()}")
    logger.info(f"Wersja: {platform.version()}")
    logger.info(f"Architektura: {platform.machine()}")
    logger.info(f"Python: {platform.python_version()}")

    # Sprawdzenie dostępności NumPy
    try:
        import numpy as np

        logger.info(f"NumPy: {np.__version__}")
    except ImportError:
        logger.warning("NumPy nie jest zainstalowany")


def check_gpu_info(cp):
    """Sprawdza dostępne informacje o GPU"""
    if cp is None:
        return

    try:
        logger.info("=== Informacje o GPU ===")
        device_count = cp.cuda.runtime.getDeviceCount()
        logger.info(f"Liczba dostępnych urządzeń CUDA: {device_count}")

        for i in range(device_count):
            device_props = cp.cuda.runtime.getDeviceProperties(i)
            logger.info(f"Urządzenie {i}:")
            logger.info(f"  Nazwa: {device_props['name'].decode()}")
            logger.info(
                f"  Pamięć całkowita: {device_props['totalGlobalMem'] / (1024**3):.2f} GB"
            )
            logger.info(f"  Multiprocesory: {device_props['multiProcessorCount']}")
            logger.info(f"  Taktowanie rdzenia: {device_props['clockRate'] / 1000} MHz")

        logger.info("✅ Wykryto urządzenia CUDA!")
    except Exception as e:
        logger.error(f"❌ Błąd podczas uzyskiwania informacji o GPU: {e}")


def run_matrix_benchmark(cp, size=2048):
    """
    Wykonuje benchmark mnożenia macierzy.

    Args:
        cp: Moduł CuPy
        size: Rozmiar macierzy (domyślnie 2048x2048)

    Returns:
        Czas wykonania lub None w przypadku błędu
    """
    if cp is None:
        return None

    try:
        import numpy as np

        logger.info(f"Tworzenie macierzy {size}x{size} dla benchmarku...")

        # Utworzenie macierzy na CPU
        a_cpu = np.random.rand(size, size).astype(np.float32)
        b_cpu = np.random.rand(size, size).astype(np.float32)

        logger.info("Przesyłanie danych do GPU...")

        # Transfer do GPU
        try:
            a_gpu = cp.asarray(a_cpu)
            b_gpu = cp.asarray(b_cpu)
        except Exception as e:
            logger.error(f"❌ Błąd transferu danych do GPU: {e}")
            return None

        # Synchronizacja
        cp.cuda.Stream.null.synchronize()

        # Pomiar czasu mnożenia macierzy na GPU
        logger.info("Wykonywanie mnożenia macierzy na GPU...")
        start_time = time.time()

        c_gpu = cp.dot(a_gpu, b_gpu)

        # Synchronizacja po operacji
        cp.cuda.Stream.null.synchronize()

        duration = time.time() - start_time

        # Zwolnienie pamięci GPU
        del a_gpu, b_gpu, c_gpu
        mempool = cp.get_default_memory_pool()
        mempool.free_all_blocks()

        logger.info(f"✅ Benchmark zakończony! Czas: {duration:.4f} sekund")

        # Wykonaj ten sam test na CPU dla porównania
        logger.info("Wykonywanie mnożenia macierzy na CPU dla porównania...")
        cpu_start_time = time.time()

        c_cpu = np.dot(a_cpu, b_cpu)

        cpu_duration = time.time() - cpu_start_time

        logger.info(f"Czas CPU: {cpu_duration:.4f} sekund")
        logger.info(f"Przyspieszenie GPU vs CPU: {cpu_duration / duration:.2f}x")

        return duration
    except Exception as e:
        logger.error(f"❌ Błąd podczas benchmarku: {e}")
        return None


def calculate_ai_score(time_val_s):
    """Oblicza wynik benchmarku AI na podstawie czasu"""
    if time_val_s is None:
        return 0
    # Wyniki dopasowane do typowej wydajności; wyższy = lepszy
    if time_val_s < 0.05:
        return 10  # High-end GPU
    elif time_val_s < 0.1:
        return 9
    elif time_val_s < 0.2:
        return 8
    elif time_val_s < 0.4:
        return 7  # Mid-range GPU / Very Fast CPU
    elif time_val_s < 0.7:
        return 6
    elif time_val_s < 1.0:
        return 5  # Decent CPU
    elif time_val_s < 1.5:
        return 4
    elif time_val_s < 2.0:
        return 3
    elif time_val_s < 3.0:
        return 2
    elif time_val_s < 5.0:
        return 1
    else:
        return 0


def main():
    """Główna funkcja testowa"""
    logger.info("==== Test benchmarku AI z CuPy ====")

    # Pokaż informacje o systemie
    get_system_info()

    # Sprawdź czy CuPy jest dostępne
    cp = test_cupy_import()

    if cp is None:
        logger.error("❌ Test nie może być kontynuowany bez CuPy.")
        return

    # Sprawdź informacje o GPU
    check_gpu_info(cp)

    # Wykonaj benchmark
    benchmark_time = run_matrix_benchmark(cp)

    # Oblicz wynik AI
    if benchmark_time is not None:
        ai_score = calculate_ai_score(benchmark_time)
        logger.info(f"==== WYNIK TESTU AI: {ai_score}/10 ====")

        # Interpretacja wyniku
        if ai_score >= 8:
            logger.info(
                "🔥 Twój GPU działa świetnie! Wysokowydajne obliczenia AI są możliwe."
            )
        elif ai_score >= 5:
            logger.info(
                "👍 Twój GPU działa dobrze. Średniowydajne obliczenia AI są możliwe."
            )
        elif ai_score > 0:
            logger.info("⚠️ Twój GPU działa, ale z ograniczoną wydajnością.")
        else:
            logger.info("❌ Test nie powiódł się lub wydajność jest bardzo niska.")
    else:
        logger.error(
            "❌ Nie można obliczyć wyniku AI - benchmark nie zakończył się pomyślnie."
        )


if __name__ == "__main__":
    main()
