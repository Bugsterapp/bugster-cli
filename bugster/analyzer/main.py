import sys

from loguru import logger

from bugster.analyzer.core.app_analyzer import AppAnalyzer, detect_supported_framework
from bugster.analyzer.core.framework_detector import detect_framework


def analyze_codebase(options: dict = {}) -> None:
    """Analyze the repository codebase."""
    # Note: Logger configuration is now handled globally by the CLI
    # The --debug flag controls logging visibility across all commands
    # Legacy show_logs parameter is maintained for backward compatibility but is ignored

    detect_framework(options=options)
    analyzer = AppAnalyzer(framework_info=detect_supported_framework())
    analyzer.execute(options=options)
