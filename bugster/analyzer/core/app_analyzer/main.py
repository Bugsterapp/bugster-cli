import json
import os

from loguru import logger

from bugster.analyzer.core.app_analyzer.nextjs_analyzer import NextjsAnalyzer
from bugster.analyzer.core.framework_detector import get_project_info
from bugster.analyzer.utils.errors import BugsterError
from bugster.constants import BUGSTER_DIR

SUPPORTED_FRAMEWORKS_IDS = ["next"]


def detect_supported_framework():
    """Detect the supported framework."""
    project_info = get_project_info()
    supported_frameworks = [
        f
        for f in project_info["data"]["frameworks"]
        if f["id"] in SUPPORTED_FRAMEWORKS_IDS
    ]

    if len(supported_frameworks) == 0:
        raise BugsterError("No supported framework found")

    if len(supported_frameworks) > 1:
        frameworks_names = ", ".join([f.name for f in supported_frameworks])
        raise BugsterError(f"Multiple supported frameworks found: {frameworks_names}")

    return supported_frameworks[0]


def get_existing_analysis(framework_id):
    """Get the existing analysis."""
    logger.info("Getting existing analysis: {}", {"frameworkId": framework_id})

    try:
        cache_framework_dir = os.path.join(BUGSTER_DIR, framework_id)
        analysis_json_path = os.path.join(cache_framework_dir, "analysis.json")

        try:
            exists = os.access(analysis_json_path, os.F_OK)

            if not exists:
                logger.info(
                    "Analysis file does not exist at: {}. Creating new analysis...",
                    analysis_json_path,
                )
                return None
        except Exception as err:
            logger.error("Failed to check if analysis file exists: {}", err)
            return None

        with open(analysis_json_path, "r", encoding="utf-8") as file:
            analysis_json = file.read()

        analysis_data = json.loads(analysis_json)
        return analysis_data["data"]
    except Exception as error:
        logger.error("Failed to read existing analysis: {}", error)
        return None


class AppAnalyzer:
    """Analyze the application and returns the analysis."""

    def __init__(self, framework_info):
        self.framework_info = framework_info

    def execute(self, options: dict = {}):
        """Execute the analysis."""
        logger.info(
            "Analyzing application: {}", {"framework": self.framework_info["id"]}
        )
        analysis = None

        if not options.get("force"):
            existing_analysis = get_existing_analysis(
                framework_id=self.framework_info["id"]
            )

            if existing_analysis:
                logger.info("Using existing analysis from cache...")
                return existing_analysis
        if self.framework_info["id"] == "next":
            analysis = self.analyze_next_js()
        else:
            raise BugsterError(f"Unsupported framework: {self.framework_info['id']}")

        logger.info("Analysis complete for {} framework", self.framework_info["name"])
        return analysis

    def analyze_next_js(self):
        """Analyze the Next.js application."""
        logger.info("Starting Next.js analysis...")

        try:
            next_analyzer = NextjsAnalyzer(framework_info=self.framework_info)
            analysis = next_analyzer.execute()
            logger.info("Next.js analysis completed successfully!")
            return analysis
        except Exception as error:
            logger.error("Failed to analyze Next.js application: {}", error)
            raise BugsterError("Failed to analyze Next.js application")
