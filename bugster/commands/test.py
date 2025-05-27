from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.status import Status
from typing import Optional, List
import time

from bugster.clients.ws_client import WebSocketClient
from bugster.clients.mcp_client import MCPStdioClient
from bugster.commands.middleware import require_api_key
from bugster.utils.file import load_config, load_test_files, get_mcp_config_path
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
    complete_message: WebSocketCompleteMessage, test_name: str, elapsed_time: float
) -> NamedTestResult:
    """Handle a complete message from the WebSocket server."""
    result = NamedTestResult(
        name=test_name,
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
                        "dir": ".bugster/videos/",
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
                        complete_message, test.name, 0
                    )  # time is added later
                    return result
                else:
                    if not silent:
                        console.print(f"[red]Internal error: {message}[/red]")
                    raise typer.Exit(1)

    finally:
        await ws_client.close()
        await mcp_client.close()


@require_api_key
async def test_command(
    test_path: Optional[str] = None,
    headless: Optional[bool] = False,
    silent: Optional[bool] = False,
):
    """Run Bugster tests."""
    total_start_time = time.time()

    try:
        # Load configuration and test files
        config = load_config()
        path = Path(test_path) if test_path else None
        test_files = load_test_files(path)

        if not test_files:
            console.print("[yellow]No test files found[/yellow]")
            return

        results = []

        # Execute each test
        for test_file in test_files:
            if not silent:
                console.print(f"\n[blue]Running tests from {test_file['file']}[/blue]")

            # Handle both single test object and list of test objects
            content = test_file["content"]
            if not isinstance(content, list):
                console.print(
                    f"[red]Error: Invalid test file format in {test_file['file']}[/red]"
                )
                continue

            for test_data in content:
                # Extract metadata before creating Test object
                metadata = (
                    test_data.pop("_metadata", {})
                    if isinstance(test_data, dict)
                    else {}
                )

                if not silent:
                    console.print(f"\n[green]Test: {test_data['name']}[/green]")

                test = Test(**test_data)
                test_start_time = time.time()
                result = await execute_test(
                    test, config, headless=headless, silent=silent
                )
                test_elapsed_time = time.time() - test_start_time

                # Add elapsed time to result
                result.time = test_elapsed_time

                status_color = "green" if result.result == "pass" else "red"
                console.print(
                    f"[{status_color}]Test: {test.name} -> {result.result} (Time: {test_elapsed_time:.2f}s)[/{status_color}]"
                )
                results.append(result)

        # Display results table
        console.print(create_results_table(results))

        # Display total time
        total_time = time.time() - total_start_time
        console.print(f"\n[blue]Total execution time: {total_time:.2f}s[/blue]")

        # Exit with non-zero status if any test failed
        if any(result.result == "fail" for result in results):
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
