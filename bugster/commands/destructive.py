import asyncio
import hashlib
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.style import Style
from rich.table import Table

from bugster.analytics import track_command
from bugster.clients.mcp_client import MCPStdioClient
from bugster.clients.ws_client import WebSocketClient
from bugster.commands.middleware import require_api_key
from bugster.commands.sync import get_current_branch
from bugster.libs.services.destructive_service import DestructiveService
from bugster.libs.services.destructive_stream_service import DestructiveStreamService
from bugster.types import (
    Config,
    NamedDestructiveResult,
    NamedDestructiveResultWithVideo,
    WebSocketDestructiveCompleteMessage,
    WebSocketInitDestructiveMessage,
    WebSocketStepRequestMessage,
    WebSocketStepResultMessage,
)
from bugster.utils.console_messages import DestructiveMessages
from bugster.utils.file import get_mcp_config_path, load_config

console = Console()

# Color palette for parallel destructive agent execution
AGENT_COLORS = [
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


def get_agent_color(agent_name: str) -> str:
    """Get a consistent color for an agent name using hash."""
    hash_value = hashlib.md5(agent_name.encode()).hexdigest()
    color_index = int(hash_value, 16) % len(AGENT_COLORS)
    return AGENT_COLORS[color_index]


def format_parallel_message(
    agent_name: str, page: str, message: str, level: str = "info"
) -> str:
    """Format message for parallel execution with color and compact format."""
    color = get_agent_color(agent_name)
    # Truncate agent name and page if too long
    display_agent = agent_name[:15] + "..." if len(agent_name) > 18 else agent_name
    display_page = page[:20] + "..." if len(page) > 23 else page

    # Color-code by level
    level_colors = {
        "info": color,
        "warning": "yellow",
        "error": "red",
        "success": "green",
    }

    level_color = level_colors.get(level, color)
    return f"[{level_color}][{display_agent:18}|{display_page:23}][/{level_color}] {message}"  # noqa: E501


def print_parallel_safe(
    agent_name: str,
    page: str,
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

    if verbose or max_concurrent == 1 or force_compact:
        console.print(format_parallel_message(agent_name, page, message, level))


async def handle_destructive_step_request(
    step_request: WebSocketStepRequestMessage,
    mcp_client: MCPStdioClient,
    ws_client: WebSocketClient,
    agent_name: str = "",
    page: str = "",
    silent: bool = False,
    max_concurrent: int = 1,
    verbose: bool = False,
) -> None:
    """Handle a step request from the WebSocket server for destructive agents."""
    print_parallel_safe(
        agent_name, page, step_request.message, "info", max_concurrent, verbose, silent
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


def handle_destructive_complete_message(
    complete_message: WebSocketDestructiveCompleteMessage,
    agent_name: str,
    page: str,
    elapsed_time: float,
) -> NamedDestructiveResult:
    """Handle a complete message from the WebSocket server for destructive agents."""
    result = NamedDestructiveResult(
        page=page,
        agent=agent_name,
        result=complete_message.result,
        time=elapsed_time,
    )
    return result


async def execute_destructive_agent(
    page: str, agent: str, diff: str, config: Config, **kwargs
) -> NamedDestructiveResult:
    """Execute a single destructive agent using WebSocket and MCP clients."""
    ws_client = WebSocketClient()
    mcp_client = MCPStdioClient()
    silent = kwargs.get("silent", False)
    run_id = kwargs.get("run_id", str(uuid.uuid4()))
    max_concurrent = kwargs.get("max_concurrent", 1)
    verbose = kwargs.get("verbose", False)

    try:
        # Connect to WebSocket and initialize MCP
        print_parallel_safe(
            agent,
            page,
            "Connecting to Bugster Agent...",
            "info",
            max_concurrent,
            verbose,
            silent,
            force_compact=True,
        )
        await ws_client.connect()
        print_parallel_safe(
            agent,
            page,
            "Connected successfully!",
            "success",
            max_concurrent,
            verbose,
            silent,
            force_compact=True,
        )

        # Initialize MCP client
        mcp_config = {
            "browser": {
                "contextOptions": {
                    "viewport": {"width": 1280, "height": 720},
                    "recordVideo": {
                        "dir": f".bugster/videos/destructive/{run_id}/{agent}_{page}",
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

        await mcp_client.init_client(mcp_command, mcp_args)

        # Send initial destructive agent data with config
        await ws_client.send(
            WebSocketInitDestructiveMessage(
                page=page,
                diff=diff,
                agent=agent,
                config=config,
            ).model_dump()
        )

        # Main destructive agent loop
        print_parallel_safe(
            agent,
            page,
            f"Starting {agent} execution",
            "info",
            max_concurrent,
            verbose,
            silent,
            force_compact=True,
        )
        return await _execute_destructive_loop(
            ws_client,
            mcp_client,
            agent,
            page,
            silent,
            max_concurrent,
            verbose,
        )

    finally:
        await ws_client.close()
        await mcp_client.close()


async def _execute_destructive_loop(
    ws_client: WebSocketClient,
    mcp_client: MCPStdioClient,
    agent: str,
    page: str,
    silent: bool,
    max_concurrent: int,
    verbose: bool,
) -> NamedDestructiveResult:
    """Execute the main destructive agent loop."""
    last_step_request = None
    timeout_retry_count = 0
    unknown_retry_count = 0
    max_retries = 2

    while True:
        try:
            message = await ws_client.receive(timeout=300)
        except asyncio.TimeoutError:
            DestructiveMessages.error("Timeout: No response from Bugster Agent")
            raise typer.Exit(1) from None

        if message.get("action") == "step_request":
            step_request = WebSocketStepRequestMessage(**message)
            last_step_request = step_request
            timeout_retry_count = 0
            unknown_retry_count = 0

            await handle_destructive_step_request(
                step_request,
                mcp_client,
                ws_client,
                agent,
                page,
                silent,
                max_concurrent,
                verbose,
            )

        elif message.get("action") == "destructive_complete":
            complete_message = WebSocketDestructiveCompleteMessage(**message)
            result = handle_destructive_complete_message(
                complete_message, agent, page, 0
            )  # time is added later
            print_parallel_safe(
                agent,
                page,
                f"Agent completed: {len(result.result.bugs)} bugs found",
                "success" if len(result.result.bugs) == 0 else "warning",
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
                    agent,
                    page,
                    f"Retrying ({timeout_retry_count}/{max_retries}): {last_step_request.message}",  # noqa: E501
                    "warning",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )

                await handle_destructive_step_request(
                    last_step_request,
                    mcp_client,
                    ws_client,
                    agent,
                    page,
                    silent,
                    max_concurrent,
                    verbose,
                )
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for step: {last_step_request.message if last_step_request else 'Unknown step'}"  # noqa: E501
                )
                print_parallel_safe(
                    agent,
                    page,
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
                    agent,
                    page,
                    f"Waiting 30s, then retrying ({unknown_retry_count}/{max_retries}): {last_step_request.message}",  # noqa: E501
                    "warning",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )

                await asyncio.sleep(30)

                print_parallel_safe(
                    agent,
                    page,
                    f"Retrying ({unknown_retry_count}/{max_retries}): {last_step_request.message}",  # noqa: E501
                    "info",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )

                await handle_destructive_step_request(
                    last_step_request,
                    mcp_client,
                    ws_client,
                    agent,
                    page,
                    silent,
                    max_concurrent,
                    verbose,
                )
            else:
                logger.error(
                    f"Max retries ({max_retries}) exceeded for unknown message. Last step: {last_step_request.message if last_step_request else 'Unknown step'}"  # noqa: E501
                )
                logger.error(f"Final unknown message: {message}")
                print_parallel_safe(
                    agent,
                    page,
                    "Internal error. Please try again later",
                    "error",
                    max_concurrent,
                    verbose,
                    silent,
                    force_compact=True,
                )
                raise typer.Exit(1)


async def execute_single_destructive_agent_with_semaphore(
    semaphore: asyncio.Semaphore,
    page: str,
    agent: str,
    diff: str,
    config: Config,
    agent_executor_kwargs: dict,
    stream_service: Optional[DestructiveStreamService],
    api_run_id: Optional[str],
    run_id: str,
    executor: ThreadPoolExecutor,
    silent: bool = False,
) -> NamedDestructiveResult:
    """Execute a single destructive agent with semaphore for concurrency control."""
    async with semaphore:
        return await execute_single_destructive_agent(
            page,
            agent,
            diff,
            config,
            agent_executor_kwargs,
            stream_service,
            api_run_id,
            run_id,
            executor,
            silent,
        )


async def execute_single_destructive_agent(
    page: str,
    agent: str,
    diff: str,
    config: Config,
    agent_executor_kwargs: dict,
    stream_service: Optional[DestructiveStreamService],
    api_run_id: Optional[str],
    run_id: str,
    executor: ThreadPoolExecutor,
    silent: bool = False,
) -> NamedDestructiveResult:
    """Execute a single destructive agent and handle streaming."""
    max_concurrent = agent_executor_kwargs.get("max_concurrent", 1)
    verbose = agent_executor_kwargs.get("verbose", False)

    print_parallel_safe(
        agent,
        page,
        "Starting destructive agent",
        "info",
        max_concurrent,
        verbose,
        silent,
        force_compact=True,
    )

    agent_start_time = time.time()
    result = await execute_destructive_agent(
        page, agent, diff, config, **agent_executor_kwargs
    )
    agent_elapsed_time = time.time() - agent_start_time

    # Add elapsed time to result
    result.time = agent_elapsed_time

    print_parallel_safe(
        agent,
        page,
        f"Finished: {len(result.result.bugs)} bugs found (Time: {agent_elapsed_time:.2f}s)",
        "success" if len(result.result.bugs) == 0 else "warning",
        max_concurrent,
        verbose,
        silent,
        force_compact=True,
    )

    # Rename the video to include agent and page info
    video_dir = Path(".bugster/videos/destructive") / run_id / f"{agent}_{page}"
    rename_destructive_video(video_dir, agent, page)

    # Stream result if enabled (in background)
    if stream_service and api_run_id:
        session_id = str(uuid.uuid4())

        # Create result with video info
        result_with_video = NamedDestructiveResultWithVideo(
            page=result.page,
            agent=result.agent,
            result=result.result,
            time=result.time,
            session_id=session_id,
        )

        video_path = get_video_path_for_destructive_agent(video_dir, agent, page)

        # Submit session creation and video upload to thread pool
        executor.submit(
            handle_destructive_result_streaming,
            stream_service,
            api_run_id,
            result_with_video,
            video_path,
        )

    return result


def create_destructive_results_table(results: list[NamedDestructiveResult]) -> Table:
    """Create a formatted table with destructive agent results."""
    table = Table(title="Destructive Agent Results")
    table.add_column("Page", justify="left")
    table.add_column("Agent", justify="left")
    table.add_column("Bugs Found", justify="center")
    table.add_column("Time (s)", justify="right")

    for result in results:
        bugs_count = len(result.result.bugs)
        table.add_row(
            result.page,
            result.agent,
            str(bugs_count),
            f"{result.time:.2f}",
            style=Style(color="green" if bugs_count == 0 else "yellow"),
        )

    return table


@require_api_key
@track_command("destructive")
async def destructive_command(
    headless: Optional[bool] = False,
    silent: Optional[bool] = False,
    stream_results: Optional[bool] = False,
    base_url: Optional[str] = None,
    max_concurrent: Optional[int] = None,
    verbose: Optional[bool] = False,
) -> None:
    """Run destructive agents to find potential bugs in changed pages."""
    total_start_time = time.time()

    try:
        # Load configuration
        config = load_config()
        if base_url:
            config.base_url = base_url

        # Initialize destructive service
        destructive_service = DestructiveService()

        if not silent:
            DestructiveMessages.analyzing_changes()

        # Get page agent assignments
        page_agents = destructive_service.get_page_agents_assignments()

        if not page_agents:
            DestructiveMessages.no_agents_assigned()
            return

        # Collect all agent tasks
        all_agent_tasks = []
        for page_agent in page_agents:
            page = page_agent.page
            diff = destructive_service.get_diff_for_page(page)

            for agent in page_agent.agents:
                all_agent_tasks.append((page, agent, diff))

        if not all_agent_tasks:
            DestructiveMessages.no_agents_assigned()
            return

        # Determine max concurrent agents (default to 3 for safety)
        max_concurrent = max_concurrent or 3
        semaphore = asyncio.Semaphore(max_concurrent)
        run_id = str(uuid.uuid4())

        # Initialize streaming service if requested
        stream_service, api_run_id = None, None
        if stream_results:
            stream_service, api_run_id = initialize_destructive_streaming_service(
                config, run_id, silent
            )

        if not silent:
            DestructiveMessages.running_agents_status(
                len(all_agent_tasks), max_concurrent
            )

        # Create thread pool executor for background operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Execute all agents concurrently
            tasks = []
            for page, agent, diff in all_agent_tasks:
                agent_executor_kwargs = {
                    "headless": headless,
                    "silent": silent,
                    "run_id": run_id,
                    "max_concurrent": max_concurrent,
                    "verbose": verbose,
                }

                task = execute_single_destructive_agent_with_semaphore(
                    semaphore,
                    page,
                    agent,
                    diff,
                    config,
                    agent_executor_kwargs,
                    stream_service,
                    api_run_id,
                    run_id,
                    executor,
                    silent,
                )
                tasks.append(task)

            if not silent:
                DestructiveMessages.executing_agents()

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    page, agent, _ = all_agent_tasks[i]
                    DestructiveMessages.error(
                        f"Agent {agent} for page {page} failed with exception: {str(result)}"
                    )
                    # Create a failed result for the exception
                    from bugster.types import Bug, DestructiveResult

                    failed_result = NamedDestructiveResult(
                        page=page,
                        agent=agent,
                        result=DestructiveResult(
                            bugs=[
                                Bug(
                                    name="Agent Execution Error",
                                    description=f"Exception: {str(result)}",
                                )
                            ]
                        ),
                        time=0,
                    )
                    final_results.append(failed_result)
                else:
                    final_results.append(result)

            if stream_results:
                DestructiveMessages.updating_final_status()

        # Display results table
        if not silent:
            console.print(create_destructive_results_table(final_results))

        # Display detailed bugs found
        total_bugs = sum(len(result.result.bugs) for result in final_results)
        if not silent and total_bugs > 0:
            DestructiveMessages.create_bugs_details_panel(final_results)

        # Display results summary
        total_time = time.time() - total_start_time

        if not silent:
            DestructiveMessages.create_results_panel(
                final_results, total_bugs, total_time
            )

        # Update final destructive run status if streaming
        finalize_destructive_streaming_run(
            stream_service, api_run_id, final_results, total_time
        )

        # Exit with code 1 if bugs were found
        if total_bugs > 0:
            raise typer.Exit(1)

    except typer.Exit:
        raise

    except Exception as e:
        DestructiveMessages.error(e)
        raise typer.Exit(1) from None


def handle_destructive_result_streaming(
    stream_service: DestructiveStreamService,
    api_run_id: str,
    result: NamedDestructiveResultWithVideo,
    video_path: Optional[Path],
):
    """Handle streaming of destructive result and video upload in background."""
    try:
        session_data = {
            "id": result.session_id,
            "page": result.page,
            "agent": result.agent,
            "bugs": [
                {"name": bug.name, "description": bug.description}
                for bug in result.result.bugs
            ],
            "time": result.time,
        }

        # Add destructive session to run
        stream_service.add_destructive_session(api_run_id, session_data)

        # Upload video if it exists
        if video_path and video_path.exists():
            video_url = stream_service.upload_video(video_path)
            if video_url:
                stream_service.update_destructive_session_with_video(
                    api_run_id, result.session_id, video_url
                )

    except Exception as e:
        DestructiveMessages.streaming_warning(f"{result.agent}|{result.page}", e)


def initialize_destructive_streaming_service(
    config: Config, run_id: str, silent: bool = False
) -> tuple[Optional[DestructiveStreamService], Optional[str]]:
    """Initialize the destructive streaming service and create initial run record."""
    try:
        stream_service = DestructiveStreamService()
        branch = get_current_branch()

        # Create initial destructive run record
        run_data = {
            "id": run_id,
            "base_url": config.base_url,
            "branch": branch,
            "status": "running",
            "bugs_count": 0,
            "time": 0,
            "destructive_sessions": [],
        }
        api_run = stream_service.create_destructive_run(run_data)
        api_run_id = api_run.get("id", run_id)

        if not silent:
            DestructiveMessages.streaming_results_to_run(api_run_id)

        return stream_service, api_run_id
    except Exception as e:
        DestructiveMessages.streaming_init_warning(e)
        return None, None


def finalize_destructive_streaming_run(
    stream_service: Optional[DestructiveStreamService],
    api_run_id: Optional[str],
    results: list[NamedDestructiveResult],
    total_time: float,
):
    """Update final destructive run status when streaming is enabled."""
    if not stream_service or not api_run_id:
        return

    try:
        total_bugs = sum(len(r.result.bugs) for r in results)
        final_run_data = {
            "bugs_count": total_bugs,
            "time": total_time,
            "status": "completed",
        }
        stream_service.update_destructive_run(api_run_id, final_run_data)
    except Exception as e:
        DestructiveMessages.streaming_init_warning(e)


def get_video_path_for_destructive_agent(
    video_dir: Path, agent: str, page: str
) -> Optional[Path]:
    """Get the video path for a destructive agent execution."""
    if not video_dir.exists():
        return None

    # Look for video files with the agent_page pattern
    video_files = list(video_dir.glob("*.webm")) + list(video_dir.glob("*.mp4"))
    if video_files:
        return video_files[0]  # Return the first video found
    return None


def rename_destructive_video(video_dir: Path, agent: str, page: str) -> None:
    """Rename the video file to include agent and page info."""
    if not video_dir.exists():
        return

    video_files = list(video_dir.glob("*.webm")) + list(video_dir.glob("*.mp4"))
    if video_files:
        original_video = video_files[0]
        clean_agent = "".join(c for c in agent if c.isalnum() or c in "-_")
        clean_page = "".join(c for c in page if c.isalnum() or c in "-_")
        new_name = f"{clean_agent}_{clean_page}{original_video.suffix}"
        new_path = video_dir / new_name

        try:
            original_video.rename(new_path)
        except OSError as e:
            logger.warning(
                f"Failed to rename video from {original_video} to {new_path}: {e}"
            )
