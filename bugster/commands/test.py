from pathlib import Path
import uuid
import typer
from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.status import Status
from typing import Optional, List
import time
import json
from concurrent.futures import ThreadPoolExecutor

from bugster.clients.ws_client import WebSocketClient
from bugster.clients.mcp_client import MCPStdioClient
from bugster.commands.middleware import require_api_key
from bugster.commands.sync import get_current_branch
from bugster.utils.file import load_config, load_test_files, get_mcp_config_path
from bugster.libs.services.results_stream_service import ResultsStreamService
from bugster.types import (
    Config,
    NamedTestResult,
    Test,
    WebSocketCompleteMessage,
    WebSocketInitTestMessage,
    WebSocketStepRequestMessage,
    WebSocketStepResultMessage,
)

console = Console()


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
        console.print(
            f"[yellow]Warning: Failed to stream result for {result.name}: {str(e)}[/yellow]"
        )


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
            console.print(f"[blue]Streaming results to run: {api_run_id}[/blue]")

        return stream_service, api_run_id
    except Exception as e:
        console.print(
            f"[yellow]Warning: Failed to initialize streaming service: {str(e)}[/yellow]"
        )
        return None, None


def finalize_streaming_run(
    stream_service: Optional[ResultsStreamService],
    api_run_id: Optional[str],
    results: List[NamedTestResult],
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
        console.print(
            f"[yellow]Warning: Failed to update final run status: {str(e)}[/yellow]"
        )


def save_results_to_json(
    output: str,
    config: Config,
    run_id: str,
    results: List[NamedTestResult],
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
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        console.print(f"\n[green]Results saved to: {output}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save results to {output}: {str(e)}[/red]")


def get_video_path_for_test(video_dir: Path, test_name: str) -> Optional[Path]:
    """Get the video path for a given test name."""
    if not video_dir.exists():
        return None

    slugified_name = test_name.lower().replace(" ", "_")
    video_filename = f"test__{slugified_name}.webm"
    video_path = video_dir / video_filename

    return video_path if video_path.exists() else None


def create_results_table(results: List[NamedTestResult]) -> Table:
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
) -> None:
    """Handle a step request from the WebSocket server."""
    if not silent:
        console.print(step_request.message)
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

    try:
        # Connect to WebSocket and initialize MCP
        with Status(
            "[yellow]Connecting to Bugster Agent. Sometimes this may take a few seconds...[/yellow]",
            spinner="dots",
        ) as status:
            await ws_client.connect()
            status.update("[green]Connected successfully!")
        # ================================
        # TODO: We should inject the config, command, args and env vars from the web socket
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
        with Status(
            f"[blue]Running test: {test.name}[/blue]", spinner="line"
        ) as status:
            while True:
                message = await ws_client.receive()

                if message.get("action") == "step_request":
                    step_request = WebSocketStepRequestMessage(**message)
                    await handle_step_request(
                        step_request, mcp_client, ws_client, silent
                    )
                    if not silent:
                        status.update(
                            f"[blue]Running test: {test.name} - {step_request.message}[/blue]"
                        )

                elif message.get("action") == "complete":
                    complete_message = WebSocketCompleteMessage(**message)
                    result = handle_complete_message(
                        complete_message, test, 0
                    )  # time is added later
                    return result
                else:
                    if not silent:
                        console.print(f"[red]Internal error: {message}[/red]")
                    raise typer.Exit(1)

    finally:
        await ws_client.close()
        await mcp_client.close()


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
    if not silent:
        console.print(f"\n[green]Test: {test.name}[/green]")

    test_start_time = time.time()
    result = await execute_test(test, config, **test_executor_kwargs)
    test_elapsed_time = time.time() - test_start_time

    # Add elapsed time to result
    result.time = test_elapsed_time

    status_color = "green" if result.result == "pass" else "red"
    console.print(
        f"[{status_color}]Test: {test.name} -> {result.result} (Time: {test_elapsed_time:.2f}s)[/{status_color}]"
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


@require_api_key
async def test_command(
    test_path: Optional[str] = None,
    headless: Optional[bool] = False,
    silent: Optional[bool] = False,
    stream_results: Optional[bool] = False,
    output: Optional[str] = None,
    run_id: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """Run Bugster tests."""
    total_start_time = time.time()

    try:
        # Load configuration and test files
        config = load_config()
        if base_url:
            # Override the base URL in the config
            # Used for CI/CD pipelines
            config.base_url = base_url
        path = Path(test_path) if test_path else None
        test_files = load_test_files(path)

        if not test_files:
            console.print("[yellow]No test files found[/yellow]")
            return

        results = []
        run_id = run_id or str(uuid.uuid4())

        # Initialize streaming service if requested
        stream_service, api_run_id = None, None
        if stream_results:
            stream_service, api_run_id = initialize_streaming_service(
                config, run_id, silent
            )

        # Create thread pool executor for background operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Execute each test
            for test_file in test_files:
                if not silent:
                    console.print(
                        f"\n[blue]Running tests from {test_file['file']}[/blue]"
                    )

                # Handle both single test object and list of test objects
                content = test_file["content"]
                if not isinstance(content, list):
                    console.print(
                        f"[red]Error: Invalid test file format in {test_file['file']}[/red]"
                    )
                    continue

                for test_data in content:
                    # Extract metadata before creating Test object
                    test = Test(**test_data)
                    test_executor_kwargs = {
                        "headless": headless,
                        "silent": silent,
                        "run_id": run_id,
                    }

                    result = await execute_single_test(
                        test,
                        config,
                        test_executor_kwargs,
                        stream_service,
                        api_run_id,
                        run_id,
                        executor,
                        silent,
                    )

                    results.append(result)

            if stream_results:
                console.print("Updating final run status")

        # Display results table
        console.print(create_results_table(results))

        # Display total time
        total_time = time.time() - total_start_time
        console.print(f"\n[blue]Total execution time: {total_time:.2f}s[/blue]")

        # Update final run status if streaming
        finalize_streaming_run(stream_service, api_run_id, results, total_time)

        # Save results to JSON if output specified
        if output:
            save_results_to_json(output, config, run_id, results, total_time)

        # Exit with non-zero status if any test failed
        if any(result.result == "fail" for result in results):
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
