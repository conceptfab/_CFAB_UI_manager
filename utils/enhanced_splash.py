"""
Enhanced splash screen with progress tracking and startup optimization.

This module provides an improved splash screen that can track application
startup progress and provide better user feedback during initialization.
"""

import logging
import time
from typing import List, Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QProgressBar, QSplashScreen

from utils.performance_optimizer import performance_monitor

logger = logging.getLogger(__name__)


class EnhancedSplashScreen(QSplashScreen):
    """
    Enhanced splash screen with progress tracking and startup optimization.

    Features:
    - Progress bar with detailed status messages
    - Startup task tracking
    - Performance monitoring integration
    - Smooth animations and transitions
    """

    progress_updated = pyqtSignal(int, str)  # progress_percentage, message
    startup_completed = pyqtSignal()

    def __init__(
        self,
        image_path: str,
        window_size: tuple = (642, 250),
        show_progress: bool = True,
        auto_close: bool = True,
    ):
        """
        Initialize the enhanced splash screen.

        Args:
            image_path: Path to the splash screen image
            window_size: Tuple of (width, height) for the splash screen
            show_progress: Whether to show progress bar
            auto_close: Whether to automatically close when startup completes
        """
        # Load and scale the image
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            # Create a default pixmap if image loading fails
            pixmap = QPixmap(*window_size)
            pixmap.fill(Qt.GlobalColor.blue)
            logger.warning(
                f"Could not load splash image from {image_path}, using default"
            )
        else:
            pixmap = pixmap.scaled(*window_size, Qt.AspectRatioMode.KeepAspectRatio)

        super().__init__(pixmap)
        self.setFixedSize(*window_size)

        self.window_size = window_size
        self.show_progress = show_progress
        self.auto_close = auto_close

        # Progress tracking
        self.current_progress = 0
        self.total_tasks = 0
        self.completed_tasks = 0
        self.startup_tasks: List[str] = []
        self.start_time = None

        # UI components
        self._init_ui_components()

        # Performance monitoring
        self.performance_stats = {}

        logger.debug("EnhancedSplashScreen initialized")

    def _init_ui_components(self):
        """Initialize UI components for the splash screen."""
        # Status message label
        self.message_label = QLabel(self)
        self.message_label.setGeometry(
            10, self.window_size[1] - 45, self.window_size[0] - 20, 20
        )
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet(
            "color: white; font-size: 11px; font-weight: bold; "
            "background-color: rgba(0, 0, 0, 50); border-radius: 3px;"
        )
        self.message_label.setText("Initializing...")

        # Progress bar
        if self.show_progress:
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setGeometry(
                10, self.window_size[1] - 25, self.window_size[0] - 20, 15
            )
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #333;
                    border-radius: 3px;
                    text-align: center;
                    font-size: 9px;
                    color: white;
                    background-color: rgba(0, 0, 0, 50);
                }
                QProgressBar::chunk {
                    background-color: #0066cc;
                    border-radius: 2px;
                }
            """
            )
        else:
            self.progress_bar = None

    @performance_monitor.measure_execution_time("splash_screen_startup")
    def start_with_tasks(self, tasks: List[str]) -> None:
        """
        Start the splash screen with a list of startup tasks.

        Args:
            tasks: List of task names that will be performed during startup
        """
        self.startup_tasks = tasks[:]
        self.total_tasks = len(tasks)
        self.completed_tasks = 0
        self.start_time = time.time()

        if self.progress_bar:
            self.progress_bar.setMaximum(self.total_tasks)
            self.progress_bar.setValue(0)

        self.show()
        self.raise_()
        self.activateWindow()

        logger.debug(f"Splash screen started with {self.total_tasks} tasks")

    def update_progress(self, task_name: str, completed: bool = True) -> None:
        """
        Update progress for a specific task.

        Args:
            task_name: Name of the task being updated
            completed: Whether the task is completed
        """
        if completed:
            self.completed_tasks += 1

        # Update progress bar
        if self.progress_bar:
            self.progress_bar.setValue(self.completed_tasks)

        # Update message
        if completed:
            progress_percentage = int(
                (self.completed_tasks / max(1, self.total_tasks)) * 100
            )
            elapsed_time = time.time() - (self.start_time or time.time())

            message = f"Completed: {task_name} ({self.completed_tasks}/{self.total_tasks}) - {elapsed_time:.1f}s"
            self.message_label.setText(message)

            self.progress_updated.emit(progress_percentage, message)

            logger.debug(
                f"Task completed: {task_name} ({self.completed_tasks}/{self.total_tasks})"
            )
        else:
            message = f"Processing: {task_name}..."
            self.message_label.setText(message)
            logger.debug(f"Task started: {task_name}")

        # Check if all tasks are completed
        if self.completed_tasks >= self.total_tasks:
            self._on_startup_completed()

    def _on_startup_completed(self) -> None:
        """Handle startup completion."""
        total_time = time.time() - (self.start_time or time.time())

        final_message = f"Startup completed in {total_time:.2f}s"
        self.message_label.setText(final_message)

        if self.progress_bar:
            self.progress_bar.setValue(self.total_tasks)

        self.startup_completed.emit()

        # Zmniejszono verbosity - komunikat przeniesiony na poziom DEBUG
        logger.debug(f"Startup completed in {total_time:.2f}s")

        # Auto-close if enabled
        if self.auto_close:
            QTimer.singleShot(1000, self.close)  # Close after 1 second

    def set_message(self, message: str) -> None:
        """Set a custom message on the splash screen."""
        self.message_label.setText(message)

    def add_performance_stat(self, operation: str, duration: float) -> None:
        """Add a performance statistic."""
        self.performance_stats[operation] = duration
        logger.debug(f"Performance stat: {operation} took {duration:.3f}s")

    def get_performance_summary(self) -> str:
        """Get a summary of performance statistics."""
        if not self.performance_stats:
            return "No performance data available"

        total_time = sum(self.performance_stats.values())
        summary_lines = [f"Total startup time: {total_time:.2f}s"]

        # Sort operations by duration (longest first)
        sorted_ops = sorted(
            self.performance_stats.items(), key=lambda x: x[1], reverse=True
        )

        for operation, duration in sorted_ops:
            percentage = (duration / total_time) * 100
            summary_lines.append(f"  {operation}: {duration:.2f}s ({percentage:.1f}%)")

        return "\n".join(summary_lines)


class StartupProgressTracker(QObject):
    """
    Tracks startup progress and integrates with splash screen.

    This class coordinates between different startup components to provide
    accurate progress reporting and performance monitoring.
    """

    task_started = pyqtSignal(str)  # task_name
    task_completed = pyqtSignal(str, float)  # task_name, duration

    def __init__(self, splash_screen: Optional[EnhancedSplashScreen] = None):
        super().__init__()
        self.splash_screen = splash_screen
        self.active_tasks = {}
        self.completed_tasks = {}

        # Connect signals if splash screen is provided
        if self.splash_screen:
            self.task_started.connect(
                lambda name: self.splash_screen.update_progress(name, completed=False)
            )
            self.task_completed.connect(
                lambda name, duration: (
                    self.splash_screen.update_progress(name, completed=True),
                    self.splash_screen.add_performance_stat(name, duration),
                )
            )

    def start_task(self, task_name: str) -> None:
        """Start tracking a task."""
        start_time = time.time()
        self.active_tasks[task_name] = start_time
        self.task_started.emit(task_name)
        logger.debug(f"Started tracking task: {task_name}")

    def complete_task(self, task_name: str) -> None:
        """Complete tracking a task."""
        if task_name in self.active_tasks:
            start_time = self.active_tasks.pop(task_name)
            duration = time.time() - start_time
            self.completed_tasks[task_name] = duration
            self.task_completed.emit(task_name, duration)
            logger.debug(f"Completed task: {task_name} in {duration:.3f}s")
        else:
            logger.warning(f"Attempted to complete unknown task: {task_name}")

    def get_task_duration(self, task_name: str) -> Optional[float]:
        """Get the duration of a completed task."""
        return self.completed_tasks.get(task_name)

    def get_total_time(self) -> float:
        """Get total time for all completed tasks."""
        return sum(self.completed_tasks.values())


# Factory function for creating optimized splash screens
def create_optimized_splash(
    image_path: str, startup_tasks: List[str], window_size: tuple = (642, 250)
) -> tuple[EnhancedSplashScreen, StartupProgressTracker]:
    """
    Create an optimized splash screen with progress tracking.

    Args:
        image_path: Path to splash screen image
        startup_tasks: List of task names for progress tracking
        window_size: Splash screen dimensions

    Returns:
        Tuple of (splash_screen, progress_tracker)
    """
    splash = EnhancedSplashScreen(
        image_path=image_path,
        window_size=window_size,
        show_progress=True,
        auto_close=True,
    )

    tracker = StartupProgressTracker(splash_screen=splash)

    # Start the splash screen with tasks
    splash.start_with_tasks(startup_tasks)

    # Zmniejszono verbosity - komunikat przeniesiony na poziom DEBUG
    logger.debug(f"Created optimized splash screen with {len(startup_tasks)} tasks")

    return splash, tracker


if __name__ == "__main__":
    # Example usage and testing
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create a test splash screen
    tasks = [
        "Loading configuration",
        "Initializing UI components",
        "Loading translations",
        "Connecting to services",
        "Finalizing startup",
    ]

    splash, tracker = create_optimized_splash(
        image_path="resources/img/splash.jpg", startup_tasks=tasks
    )

    # Simulate startup tasks
    def simulate_startup():
        import time

        for i, task in enumerate(tasks):
            time.sleep(0.5)  # Simulate work
            tracker.start_task(task)
            time.sleep(0.5)  # Simulate more work
            tracker.complete_task(task)

    # Run simulation in a timer
    timer = QTimer()
    timer.timeout.connect(simulate_startup)
    timer.setSingleShot(True)
    timer.start(1000)

    app.exec()
