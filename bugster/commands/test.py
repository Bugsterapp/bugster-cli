import asyncio
import hashlib
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse

import typer
from loguru import logger
from rich.console import Console
from rich.style import Style
from rich.table import Table

from bugster.analytics import track_command
from bugster.clients.http_client import BugsterHTTPClient
from bugster.clients.mcp_client import MCPStdioClient
from bugster.clients.ws_client import WebSocketClient
from bugster.commands.middleware import require_api_key
from bugster.commands.sync import get_current_branch
from bugster.libs.services.results_stream_service import ResultsStreamService
from bugster.libs.services.run_limits_service import (
    apply_test_limit,
    count_total_tests,
)
from bugster.libs.services.update_service import DetectAffectedSpecsService
from bugster.types import (
    Config,
    NamedTestResult,
    Test,
    WebSocketCompleteMessage,
    WebSocketInitTestMessage,
    WebSocketStepRequestMessage,
    WebSocketStepResultMessage,
)
from bugster.utils.console_messages import RunMessages
from bugster.utils.file import (
    check_and_update_project_commands,
    get_mcp_config_path,
    load_always_run_tests,
    load_config,
    load_test_execution_config,
    load_test_files,
    merge_always_run_with_affected_tests,
)
from bugster.utils.user_config import get_api_key

console = Console()
# Color palette for parallel test execution
TEST_COLORS = [
    "cyan",
    "magenta",
    "yellow",
    "green",
    "blue",
    "red",
    "bright_cyan",
    "bright_magenta",
    "bright_yellow",
    "bright_green",
    "bright_blue",
    "bright_red",
]


def get_test_color(test_name: str) -> str:
    """Get a consistent color for a test name using hash."""
    hash_value = hashlib.md5(test_name.encode()).hexdigest()
    color_index = int(hash_value, 16) % len(TEST_COLORS)
    return TEST_COLORS[color_index]


def format_parallel_message(test_name: str, message: str, level: str = "info") -> str:
    """Format message for parallel execution with color and compact format."""
    color = get_test_color(test_name)
    # Truncate test name if too long
    display_name = test_name[:20] + "..." if len(test_name) > 23 else test_name

    # Color-code by level
    level_colors = {
        "info": color,
        "warning": "yellow",
        "error": "red",
        "success": "green",
    }

    level_color = level_colors.get(level, color)
    return f"[{level_color}][{display_name:23}][/{level_color}] {message}"


def should_show_detailed_logs(max_concurrent: int, verbose: bool) -> bool:
    """Determine if detailed logs should be shown based on concurrency and verbosity."""
    return verbose or max_concurrent == 1


def print_parallel_safe(
    test_name: str,
    message: str,
    level: str = "info",
    max_concurrent: int = 1,
    verbose: bool = False,
    silent: bool = False,
    force_compact: bool = False,
):
    """Print message in a parallel-safe way with appropriate formatting."""
    if silent:
        return

    if should_show_detailed_logs(max_concurrent, verbose) or force_compact:
        # Detailed mode or explicitly marked for compact mode: show message
        console.print(format_parallel_message(test_name, message, level))


def handle_test_result_streaming(
    stream_service: ResultsStreamService,
    api_run_id: str,
    result: NamedTestResult,
    video_path: Optional[Path],
):
    """Handle streaming of test result and video upload in background."""
    try:
        test_case_data = {
            "id": result.metadata.id,
            "name": result.name,
            "result": result.result,
            "reason": result.reason,
            "time": result.time,
        }

        # Add test case to run
        stream_service.add_test_case(api_run_id, test_case_data)

        # Upload video if it exists
        if video_path and video_path.exists():
            video_url = stream_service.upload_video(video_path)
            if video_url:
                stream_service.update_test_case_with_video(
                    api_run_id, result.metadata.id, video_url
                )

    except Exception as e:
        RunMessages.streaming_warning(result.name, e)


def initialize_streaming_service(
    config: Config, run_id: str, silent: bool = False
) -> tuple[Optional[ResultsStreamService], Optional[str]]:
    """Initialize the streaming service and create initial run record."""
    try:
        stream_service = ResultsStreamService()
        branch = get_current_branch()

        # Create initial run record
        run_data = {
            "id": run_id,
            "base_url": config.base_url,
            "branch": branch,
            "result": "running",
            "time": 0,
            "test_cases": [],
        }
        api_run = stream_service.create_run(run_data)
        api_run_id = api_run.get("id", run_id)

        if not silent:
            RunMessages.streaming_results_to_run(api_run_id)

        return stream_service, api_run_id
    except Exception as e:
        RunMessages.streaming_init_warning(e)
        return None, None


def finalize_streaming_run(
    stream_service: Optional[ResultsStreamService],
    api_run_id: Optional[str],
    results: list[NamedTestResult],
    total_time: float,
):
    """Update final run status when streaming is enabled."""
    if not stream_service or not api_run_id:
        return

    try:
        overall_result = "pass" if all(r.result == "pass" for r in results) else "fail"
        final_run_data = {"result": overall_result, "time": total_time}
        stream_service.update_run(api_run_id, final_run_data)
    except Exception as e:
        RunMessages.streaming_init_warning(e)


def save_results_to_json(
    output: str,
    config: Config,
    run_id: str,
    results: list[NamedTestResult],
    total_time: float,
):
    """Save test results to JSON file."""
    try:
        output_data = {
            "id": run_id,
            "base_url": config.base_url,
            "project_id": config.project_id,
            "branch": get_current_branch(),
            "result": "pass" if all(r.result == "pass" for r in results) else "fail",
            "time": total_time,
            "test_cases": [
                {
                    "id": r.metadata.id,
                    "name": r.name,
                    "result": r.result,
                    "reason": r.reason,
                    "time": r.time,
                    "video": "",  # Video URLs would need to be tracked separately
                }
                for r in results
            ],
        }

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        RunMessages.results_saved(output)
    except Exception as e:
        RunMessages.save_results_error(output, e)


def get_video_path_for_test(video_dir: Path, test_name: str) -> Optional[Path]:
    """Get the video path for a given test name."""
    if not video_dir.exists():
        return None

    slugified_name = test_name.lower().replace(" ", "_")
    video_filename = f"test__{slugified_name}.webm"
    video_path = video_dir / video_filename

    return video_path if video_path.exists() else None


def create_results_table(results: list[NamedTestResult]) -> Table:
    """Create a formatted table with test results."""
    table = Table(title="Test Results")
    table.add_column("Name", justify="left")
    table.add_column("Result", justify="left")
    table.add_column("Reason", justify="left")
    table.add_column("Time (s)", justify="right")

    for result in results:
        table.add_row(
            result.name,
            result.result,
            result.reason,
            f"{result.time:.2f}" if hasattr(result, "time") else "N/A",
            style=Style(color="green" if result.result == "pass" else "red"),
        )

    return table


async def handle_step_request(
    step_request: WebSocketStepRequestMessage,
    mcp_client: MCPStdioClient,
    ws_client: WebSocketClient,
    silent: bool = False,
    max_concurrent: int = 1,
    verbose: bool = False,
    test_name: str = "",
) -> None:
    """Handle a step request from the WebSocket server."""
    # Print step details using consistent parallel-safe formatting
    print_parallel_safe(
        test_name, step_request.message, "info", max_concurrent, verbose, silent
    )

    result = await mcp_client.execute(step_request.tool)

    await ws_client.send(
        WebSocketStepResultMessage(
            job_id=step_request.job_id,
            tool=step_request.tool,
            status="success" if not result.isError else "error",
            output=str(result.content[0].model_dump()) if result.content else "",
        ).model_dump()
    )


def handle_complete_message(
    complete_message: WebSocketCompleteMessage, test: Test, elapsed_time: float
) -> NamedTestResult:
    """Handle a complete message from the WebSocket server."""
    result = NamedTestResult(
        name=test.name,
        metadata=test.metadata,
        result=complete_message.result.result,
        reason=complete_message.result.reason,
    )
    result.time = elapsed_time  # Add time attribute
    return result


async def execute_test(test: Test, config: Config, **kwargs) -> NamedTestResult:
    """Execute a single test using WebSocket and MCP clients."""
    ws_client = WebSocketClient()
    mcp_client = MCPStdioClient()
    silent = kwargs.get("silent", False)
    run_id = kwargs.get("run_id", str(uuid.uuid4()))
    max_concurrent = kwargs.get("max_concurrent", 1)
    verbose = kwargs.get("verbose", False)

    try:
        # Connect to WebSocket and initialize MCP
        print_parallel_safe(
            test.name,
            "Connecting to Bugster Agent...",
            "info",
            max_concurrent,
            verbose,
            silent,
            force_compact=True,
        )
        await ws_client.connect()
        print_parallel_safe(
            test.name,
            "Connected successfully!",
            "success",
            max_concurrent,
            verbose,
            silent,
            force_compact=True,
        )

        # ================================
        # TODO: We should inject the config, command, args and env vars from the web socket  # noqa: E501
        mcp_config = {
            "browser": {
                "contextOptions": {
                    "viewport": {"width": 1280, "height": 720},
                    "recordVideo": {
                        "dir": f".bugster/videos/{run_id}/{test.metadata.id}",
                        "size": {"width": 1280, "height": 720},
                    },
                }
            }
        }
        playwright_config = get_mcp_config_path(mcp_config, version="v1")
        mcp_command = "npx"
        mcp_args = [
            "@playwright/mcp@latest",
            "--isolated",
            "--no-sandbox",
            "--config",
            playwright_config,
        ]
        if kwargs.get("headless"):
            mcp_args.append("--headless")
        # ================================
        await mcp_client.init_client(mcp_command, mcp_args)

        # Send initial test data with config
        await ws_client.send(
            WebSocketInitTestMessage(
                test=test,
                config=config,
            ).model_dump()
        )

        # Main test loop
        print_parallel_safe(
            test.name,
            "Starting test execution",
            "info",
            max_concurrent,
            verbose,
            silent,
            force_compact=True,
        )
        return await _execute_test_loop(
            ws_client,
            mcp_client,
            test,
            silent,
            max_concurrent,
            verbose,
        )

    finally:
        # Wrap client cleanup in try-except to prevent cleanup exceptions
        # from affecting the test result
        try:
            await ws_client.close()
        except Exception as e:
            # Log the exception but don't let it bubble up
            logger.warning(f"Error closing WebSocket client for test {test.name}: {e}")

        try:
            await mcp_client.close()
        except Exception as e:
            # Log the exception but don't let it bubble up
            logger.warning(f"Error closing MCP client for test {test.name}: {e}")


async def _execute_test_loop(
    ws_client: WebSocketClient,
    mcp_client: MCPStdioClient,
    test: Test,
    silent: bool,
    max_concurrent: int,
    verbose: bool,
) -> NamedTestResult:
    """Execute the main test loop."""
    last_step_request = None
    timeout_retry_count = 0
    unknown_retry_count = 0
    max_retries = 2

    while True:
        try:
            message = await ws_client.receive(timeout=300)
        except asyncio.TimeoutError:
            RunMessages.error("Timeout: No response from Bugster Agent")
            raise typer.Exit(1) from None

        if message.get("action") == "step_request":
            step_request = WebSocketStepRequestMessage(**message)
            last_step_request = step_request
            timeout_retry_count = 0  # Reset retry count for new step
            unknown_retry_count = 0  # Reset retry count for new step

            await handle_step_request(
                step_request,
                mcp_client,
                ws_client,
                silent,
                max_concurrent,
                verbose,
                test.name,
            )

        elif message.get("action") == "complete":
            complete_message = WebSocketCompleteMessage(**message)
            result = handle_complete_message(
                complete_message, test, 0
            )  # time is added later
            print_parallel_safe(
                test.name,
                f"Test completed: {result.result}",
                "success" if result.result == "pass" else "error",
                max_concurrent,
                verbose,
                silent,
                force_compact=True,
            )
            return result
        elif message.get("message") == "Endpoint request timed out":
            if last_step_request and timeout_retry_count < max_retries:
                timeout_retry_count += 1
                logger.warning(
                    f"Timeout occurred, retrying step ({timeout_retry_count}/{max_retries}): {last_step_request.message}"  # noqa: E501
                )
                print_parallel_safe(
                    test.name,
                    f"Retrying ({timeout_retry_count}/{max_retries}): {last_step_request.message}",  # noqa: E501
                    "warning",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )

                await handle_step_request(
                    last_step_request,
                    mcp_client,
                    ws_client,
                    silent,
                    max_concurrent,
                    verbose,
                    test.name,
                )
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for step: {last_step_request.message if last_step_request else 'Unknown step'}"  # noqa: E501
                )
                print_parallel_safe(
                    test.name,
                    "Max retries exceeded. Please try again later",
                    "error",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )
                raise typer.Exit(1)
        else:
            if last_step_request and unknown_retry_count < max_retries:
                unknown_retry_count += 1
                logger.warning(
                    f"Unknown message received, waiting 30s and retrying step ({unknown_retry_count}/{max_retries}): {last_step_request.message}"  # noqa: E501
                )
                logger.debug(f"Unknown message content: {message}")
                print_parallel_safe(
                    test.name,
                    f"Waiting 30s, then retrying ({unknown_retry_count}/{max_retries}): {last_step_request.message}",  # noqa: E501
                    "warning",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )

                await asyncio.sleep(30)

                print_parallel_safe(
                    test.name,
                    f"Retrying ({unknown_retry_count}/{max_retries}): {last_step_request.message}",  # noqa: E501
                    "info",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )

                await handle_step_request(
                    last_step_request,
                    mcp_client,
                    ws_client,
                    silent,
                    max_concurrent,
                    verbose,
                    test.name,
                )
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for unknown message. Last step: {last_step_request.message if last_step_request else 'Unknown step'}"  # noqa: E501
                )
                logger.error(f"Final unknown message: {message}")
                print_parallel_safe(
                    test.name,
                    "Internal error. Please try again later",
                    "error",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )
                raise typer.Exit(1)


def rename_video(video_dir: Path, test_name: str) -> None:
    """Rename video files to include the test name."""
    # There is not way to identify the video file corresponding to the test
    # so after the test run, we need to rename the new video to the test name
    if video_dir.exists():
        # Find video files that don't start with "test"
        for video_file in video_dir.glob("*.webm"):
            if not video_file.name.startswith("test"):
                # Create new filename with test name, slugified
                slugified_name = test_name.lower().replace(" ", "_")
                new_name = f"test__{slugified_name}.webm"
                new_path = video_dir / new_name
                # Rename the file
                video_file.rename(new_path)
                break


async def execute_single_test(
    test: Test,
    config: Config,
    test_executor_kwargs: dict,
    stream_service: Optional[ResultsStreamService],
    api_run_id: Optional[str],
    run_id: str,
    executor: ThreadPoolExecutor,
    silent: bool = False,
) -> NamedTestResult:
    """Execute a single test and handle streaming."""
    max_concurrent = test_executor_kwargs.get("max_concurrent", 1)
    verbose = test_executor_kwargs.get("verbose", False)

    print_parallel_safe(
        test.name,
        "Starting test",
        "info",
        max_concurrent,
        verbose,
        silent,
        force_compact=True,
    )

    test_start_time = time.time()
    result = await execute_test(test, config, **test_executor_kwargs)
    test_elapsed_time = time.time() - test_start_time

    # Add elapsed time to result
    result.time = test_elapsed_time

    print_parallel_safe(
        test.name,
        f"Finished: {result.result} (Time: {test_elapsed_time:.2f}s)",
        "success" if result.result == "pass" else "error",
        max_concurrent,
        verbose,
        silent,
        force_compact=True,
    )

    # Rename the video to the test name
    video_dir = Path(".bugster/videos") / run_id / test.metadata.id
    rename_video(video_dir, test.name)

    # Stream result if enabled (in background)
    if stream_service and api_run_id:
        video_path = get_video_path_for_test(video_dir, test.name)

        # Submit both test case creation and video upload to thread pool
        executor.submit(
            handle_test_result_streaming,
            stream_service,
            api_run_id,
            result,
            video_path,
        )

    return result


async def execute_single_test_with_semaphore(
    semaphore: asyncio.Semaphore,
    test: Test,
    config: Config,
    test_executor_kwargs: dict,
    stream_service: Optional[ResultsStreamService],
    api_run_id: Optional[str],
    run_id: str,
    executor: ThreadPoolExecutor,
    silent: bool = False,
) -> NamedTestResult:
    """Execute a single test with semaphore for concurrency control."""
    async with semaphore:
        return await execute_single_test(
            test,
            config,
            test_executor_kwargs,
            stream_service,
            api_run_id,
            run_id,
            executor,
            silent,
        )


def apply_vercel_protection_bypass(config: Config) -> Config:
    """Apply x-vercel-protection-bypass query parameter to base_url if present in config."""  # noqa: E501
    if not config.x_vercel_protection_bypass:
        return config

    # Parse the URL
    parsed_url = urlparse(config.base_url)

    # Add the query parameter
    query_params = {
        "x-vercel-protection-bypass": config.x_vercel_protection_bypass,
        "x-vercel-set-bypass-cookie": "true",
    }

    # Encode query parameters
    encoded_params = urlencode(query_params)

    # Reconstruct the URL with the query parameter
    modified_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            encoded_params,
            parsed_url.fragment,
        )
    )

    # Create a copy of the config with the modified base_url
    config_dict = config.model_dump()
    config_dict["base_url"] = modified_url
    return Config(**config_dict)


@require_api_key
@track_command("run")
async def test_command(
    test_path: Optional[str] = None,
    headless: Optional[bool] = None,
    silent: Optional[bool] = None,
    stream_results: bool = True,
    output: Optional[str] = None,
    run_id: Optional[str] = None,
    base_url: Optional[str] = None,
    only_affected: Optional[bool] = None,
    max_concurrent: Optional[int] = None,
    verbose: Optional[bool] = None,
    limit: Optional[int] = None,
) -> None:
    """Run Bugster tests."""
    total_start_time = time.time()

    try:
        # Load configuration and test files
        config = load_config()

        # Load test execution configuration with CLI options taking precedence
        exec_config = load_test_execution_config(
            config=config,
            headless=headless,
            silent=silent,
            verbose=verbose,
            only_affected=only_affected,
            max_concurrent=max_concurrent,
            output=output,
            limit=limit,
        )

        # Use resolved configuration values
        headless = exec_config["headless"]
        silent = exec_config["silent"]
        verbose = exec_config["verbose"]
        only_affected = exec_config["only_affected"]
        max_concurrent = exec_config["max_concurrent"]
        output = exec_config["output"]
        max_tests = exec_config["limit"]

        if base_url:
            # Override the base URL in the config
            # Used for CI/CD pipelines
            config.base_url = base_url

        # Apply Vercel protection bypass query parameter if present
        config = apply_vercel_protection_bypass(config)

        path = Path(test_path) if test_path else None

        # Load always-run tests from config
        always_run_tests = load_always_run_tests(config)

        if only_affected:
            try:
                affected_tests = DetectAffectedSpecsService().run()
                # Merge affected tests with always-run tests
                test_files = merge_always_run_with_affected_tests(
                    affected_tests, always_run_tests
                )
            except Exception as e:
                RunMessages.error(
                    f"Failed to detect affected specs: {e}. \nRunning all tests..."
                )
                test_files = load_test_files(path)
                # Still merge with always-run tests
                test_files = merge_always_run_with_affected_tests(
                    test_files, always_run_tests
                )
        else:
            test_files = load_test_files(path)
            # Merge all tests with always-run tests
            test_files = merge_always_run_with_affected_tests(
                test_files, always_run_tests
            )

        if not test_files:
            RunMessages.no_tests_found()
            return

        # Separate always-run tests from regular tests
        regular_tests = [tf for tf in test_files if not tf.get("always_run", False)]
        always_run_tests_list = [tf for tf in test_files if tf.get("always_run", False)]

        # Apply limit only to regular tests (not always-run)
        original_count = count_total_tests(regular_tests)
        limited_regular_tests, folder_distribution = apply_test_limit(
            regular_tests, max_tests
        )
        selected_count = count_total_tests(limited_regular_tests)

        # Combine limited regular tests with always-run tests
        final_test_files = always_run_tests_list + limited_regular_tests
        total_final_count = count_total_tests(final_test_files)

        # Print test limit information if limiting was applied
        if int(original_count) > int(max_tests):
            always_run_count = count_total_tests(always_run_tests_list)

            # Calculate folder distribution for always-run tests
            always_run_distribution = {}
            for test_file in always_run_tests_list:
                folder = test_file["file"].parent.name
                always_run_distribution[folder] = always_run_distribution.get(
                    folder, 0
                ) + len(test_file["content"])

            console.print(
                RunMessages.create_test_limit_panel(
                    original_count=original_count,
                    selected_count=selected_count,
                    max_tests=max_tests,
                    folder_distribution=folder_distribution,
                    always_run_count=always_run_count,
                    always_run_distribution=always_run_distribution,
                )
            )

        # Show always-run information
        if always_run_tests_list:
            always_run_count = count_total_tests(always_run_tests_list)
            console.print(
                f"[dim]Always-run tests: {always_run_count} (additional to limit)[/dim]"
            )
            console.print(
                f"[dim]Total tests to run: {total_final_count} (regular: {selected_count} + always-run: {always_run_count})[/dim]"
            )

        # Use the final combined test files for execution
        test_files = final_test_files
        run_id = run_id or str(uuid.uuid4())

        # Initialize streaming service if requested
        stream_service, api_run_id = None, None
        if stream_results:
            stream_service, api_run_id = initialize_streaming_service(
                config, run_id, silent
            )

        # Collect all tests first
        all_tests = []
        for test_file in test_files:
            if not silent:
                RunMessages.running_test_file(test_file["file"])

            # Handle both single test object and list of test objects
            content = test_file["content"]
            if not isinstance(content, list):
                RunMessages.invalid_test_file_format(test_file["file"])
                continue

            for test_data in content:
                test = Test(**test_data)
                all_tests.append((test, test_file["file"]))

        if not all_tests:
            RunMessages.no_tests_found()
            return

        # Determine max concurrent tests (default to 3 for safety)
        max_concurrent = max_concurrent or 3
        semaphore = asyncio.Semaphore(max_concurrent)

        if not silent:
            RunMessages.running_test_status(
                f"{len(all_tests)} tests", f"max {max_concurrent} concurrent"
            )

        # Create thread pool executor for background operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Create tasks for all tests
            tasks = []
            for test, _source_file in all_tests:
                test_executor_kwargs = {
                    "headless": headless,
                    "silent": silent,
                    "run_id": run_id,
                    "max_concurrent": max_concurrent,
                    "verbose": verbose,
                }

                task = execute_single_test_with_semaphore(
                    semaphore,
                    test,
                    config,
                    test_executor_kwargs,
                    stream_service,
                    api_run_id,
                    run_id,
                    executor,
                    silent,
                )
                tasks.append(task)

            # Execute all tests concurrently
            if not silent:
                RunMessages.running_test_status("Executing tests...")

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    test_name = all_tests[i][0].name
                    RunMessages.error(
                        f"Test {test_name} failed with exception: {str(result)}"
                    )
                    # Create a failed result for the exception
                    failed_result = NamedTestResult(
                        name=test_name,
                        metadata=all_tests[i][0].metadata,
                        result="fail",
                        reason=f"Exception: {str(result)}",
                    )
                    failed_result.time = 0
                    final_results.append(failed_result)
                else:
                    final_results.append(result)

            if stream_results:
                RunMessages.updating_final_status()

        # Display results table
        RunMessages.create_results_table(final_results)

        # Display results panel
        RunMessages.create_results_panel(final_results)

        # Display total time
        total_time = time.time() - total_start_time
        RunMessages.total_execution_time(total_time)

        # Update final run status if streaming
        finalize_streaming_run(stream_service, api_run_id, final_results, total_time)

        # Save results to JSON if output specified
        if output:
            save_results_to_json(output, config, run_id, final_results, total_time)

        if any(result.result == "fail" for result in final_results):
            raise typer.Exit(1)

    except typer.Exit:
        raise

    except Exception as e:
        RunMessages.error(e)
        raise typer.Exit(1) from None
    finally:
        is_first_run = check_and_update_project_commands(command_name="test")

        if is_first_run:
            with BugsterHTTPClient() as client:
                client.set_headers({"x-api-key": get_api_key()})
                client.patch(
                    "/api/v1/users/me/onboarding-status",
                    json={"run": "completed"},
                )
