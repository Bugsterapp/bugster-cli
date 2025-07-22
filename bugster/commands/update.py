import typer
from rich.console import Console

from bugster.analytics import track_command
from bugster.commands.middleware import require_api_key
from bugster.libs.services.update_service import (
    get_update_service,
)

console = Console()


@require_api_key
@track_command("update")
def update_command(
    update_only: bool = False,
    suggest_only: bool = False,
    delete_only: bool = False,
    show_logs: bool = False,
    against_default: bool = False,
    against_last_update: bool = False,
):
    """Run Bugster CLI update command."""
    # Note: Logger configuration is now handled globally by the CLI
    # The --debug flag controls logging visibility across all commands
    # Legacy show_logs parameter is maintained for backward compatibility but is ignored

    # Validate flags
    if against_default and against_last_update:
        console.print(
            "[red]Error: Cannot use both --against-default and --against-last-update flags simultaneously[/red]"
        )
        raise typer.Exit(1)

    assert sum([update_only, suggest_only, delete_only]) <= 1, (
        "At most one of update_only, suggest_only, delete_only can be True"
    )

    try:
        # Handle against_last_update logic
        if against_last_update:
            from bugster.libs.utils.update_tracker import has_last_update_state

            if not has_last_update_state():
                console.print(
                    "[yellow]Warning: No previous update state found. Running against default branch instead.[/yellow]"
                )
                against_last_update = False
                against_default = True

        console.print("✓ Analyzing code changes...")
        update_service = get_update_service(
            update_only=update_only,
            suggest_only=suggest_only,
            delete_only=delete_only,
            against_default=against_default,
            against_last_update=against_last_update,
        )
        update_service.run()

        # Save the current state after successful update
        from bugster.libs.utils.update_tracker import save_update_state

        save_update_state()
        console.print("✓ Update state saved")

    except Exception as err:
        console.print(f"[red]Error: {str(err)}[/red]")
        raise typer.Exit(1)
