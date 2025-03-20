"""Metrics manager module for the TrailBlazeApp-Scrapers project."""

from typing import Dict, List, Tuple, Optional, Literal, Union, Callable, Any
from colorama import Fore, Style, init
from emoji import emojize
from app.logging_manager import get_logger

# Initialize colorama
init(autoreset=True)


class MetricsManager:
    """
    Manages metrics collection, validation, and display.

    Provides methods for tracking and validating metrics related to the scraping process,
    and displaying them in a user-friendly format with colors and emojis.
    """

    # Standard metrics that should be tracked by all scrapers
    STANDARD_METRICS = [
        "raw_event_rows",
        "initial_events",
        "final_events",
        "multi_day_events",
        "database_inserts",
        "database_updates",
        "cache_hits",
        "cache_misses"
    ]

    def __init__(self, source_name: str) -> None:
        """
        Initialize the MetricsManager.

        Args:
            source_name (str): Name of the data source (e.g., "AERC", "SERA")
        """
        self.source_name = source_name
        self.metrics: Dict[str, int] = {metric: 0 for metric in self.STANDARD_METRICS}
        self.logger = get_logger(f"{__name__}.{source_name}")

    def increment(self, metric_name: str, value: int = 1) -> None:
        """
        Increment a metric by the specified value.

        Args:
            metric_name (str): Name of the metric to increment
            value (int): Value to increment by (default: 1)

        Raises:
            KeyError: If the metric name is not recognized
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = 0
            self.logger.warning(
                f"Created new metric '{metric_name}' that wasn't in standard metrics",
                ":warning:"
            )

        self.metrics[metric_name] += value

    def set(self, metric_name: str, value: int) -> None:
        """
        Set a metric to the specified value.

        Args:
            metric_name (str): Name of the metric to set
            value (int): Value to set the metric to

        Raises:
            KeyError: If the metric name is not recognized
        """
        if metric_name not in self.metrics:
            self.logger.warning(
                f"Created new metric '{metric_name}' that wasn't in standard metrics",
                ":warning:"
            )

        self.metrics[metric_name] = value

    def get(self, metric_name: str) -> int:
        """
        Get the current value of a metric.

        Args:
            metric_name (str): Name of the metric to get

        Returns:
            int: Current value of the metric

        Raises:
            KeyError: If the metric name is not recognized
        """
        return self.metrics.get(metric_name, 0)

    def reset(self) -> None:
        """Reset all metrics to zero."""
        for metric in self.metrics:
            self.metrics[metric] = 0

    def reset_event_metrics(self) -> None:
        """Reset only event-related metrics to zero."""
        event_metrics = [
            "raw_event_rows",
            "initial_events",
            "final_events",
            "multi_day_events"
        ]
        for metric in event_metrics:
            self.metrics[metric] = 0

    def validate_metrics(self) -> List[str]:
        """
        Validate metrics for consistency and expected values.

        Performs checks to ensure metrics are consistent with each other.
        For example, initial_events - multi_day_events should equal final_events.

        Returns:
            List[str]: List of validation error messages, empty if all validations pass
        """
        validation_errors = []

        # Check if initial_events - multi_day_events equals final_events
        if (self.metrics["initial_events"] - self.metrics["multi_day_events"] !=
                self.metrics["final_events"]):
            validation_errors.append(
                f"Data discrepancy: initial_events ({self.metrics['initial_events']}) - "
                f"multi_day_events ({self.metrics['multi_day_events']}) != "
                f"final_events ({self.metrics['final_events']})"
            )

        # Check if raw_event_rows matches initial_events
        if self.metrics["raw_event_rows"] != self.metrics["initial_events"]:
            validation_errors.append(
                f"Data discrepancy: raw_event_rows ({self.metrics['raw_event_rows']}) != "
                f"initial_events ({self.metrics['initial_events']})"
            )

        # Check if database operations match final events
        if (self.metrics["database_inserts"] + self.metrics["database_updates"] !=
                self.metrics["final_events"]):
            validation_errors.append(
                f"Database discrepancy: database_inserts ({self.metrics['database_inserts']}) + "
                f"database_updates ({self.metrics['database_updates']}) != "
                f"final_events ({self.metrics['final_events']})"
            )

        return validation_errors

    def display_metrics(self, include_validation: bool = True) -> None:
        """
        Display collected metrics in a user-friendly format with colors and emojis.

        Args:
            include_validation (bool): Whether to include validation checks (default: True)
        """
        # Header
        print(f"\n{Fore.CYAN}{Style.BRIGHT}" +
              emojize(f":rocket: Scraping Summary for {self.source_name} :rocket:", language='alias') +
              f"{Style.RESET_ALL}")

        # Event metrics
        print(f"{Fore.BLUE}{Style.BRIGHT}Event Metrics:{Style.RESET_ALL}")
        print(emojize(f":scroll: Raw Event Rows Found: {self.metrics['raw_event_rows']}", language='alias'))
        print(emojize(f":calendar: Initial Events Extracted: {self.metrics['initial_events']}", language='alias'))
        print(emojize(f":sparkles: Final Events (Consolidated): {self.metrics['final_events']}", language='alias'))
        print(emojize(f":date: Multi-Day Events: {self.metrics['multi_day_events']}", language='alias'))

        # Database metrics
        print(f"\n{Fore.BLUE}{Style.BRIGHT}Database Metrics:{Style.RESET_ALL}")
        print(emojize(f":floppy_disk: Database Inserts: {self.metrics['database_inserts']}", language='alias'))
        print(emojize(f":arrows_counterclockwise: Database Updates: {self.metrics['database_updates']}", language='alias'))

        # Cache metrics
        print(f"\n{Fore.BLUE}{Style.BRIGHT}Cache Metrics:{Style.RESET_ALL}")
        print(emojize(f":white_check_mark: Cache Hits: {self.metrics['cache_hits']}", language='alias'))
        print(emojize(f":x: Cache Misses: {self.metrics['cache_misses']}", language='alias'))

        # Any custom metrics
        custom_metrics = [m for m in self.metrics if m not in self.STANDARD_METRICS]
        if custom_metrics:
            print(f"\n{Fore.BLUE}{Style.BRIGHT}Custom Metrics:{Style.RESET_ALL}")
            for metric in custom_metrics:
                print(f"{metric}: {self.metrics[metric]}")

        # Validation
        if include_validation:
            validation_errors = self.validate_metrics()
            if not validation_errors:
                print(f"\n{Fore.GREEN}{Style.BRIGHT}" +
                      emojize(":white_check_mark: All counts are valid!", language='alias') +
                      f"{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}{Style.BRIGHT}Validation Errors:{Style.RESET_ALL}")
                for error in validation_errors:
                    print(emojize(f":warning: {Fore.YELLOW}{error}{Style.RESET_ALL}", language='alias'))

    def get_all_metrics(self) -> Dict[str, int]:
        """
        Get all metrics as a dictionary.

        Returns:
            Dict[str, int]: Dictionary of all metrics
        """
        return self.metrics.copy()
