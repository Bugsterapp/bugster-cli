"""
Sync command implementation.
"""

from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.status import Status
import subprocess
from datetime import datetime
import click

from bugster.libs.services.specs_service import SpecsService
from bugster.commands.middleware import require_api_key
from bugster.utils.yaml_spec import (
    load_yaml_specs,
    save_yaml_specs,
    YamlSpec,
    SpecMetadata,
)
from bugster.constants import TESTS_DIR

console = Console()


def get_current_branch() -> str:
    """Get the current git branch name or return 'main' if git is not available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "main"


def sync_specs(
    specs_service: SpecsService,
    branch: str,
    local_specs: dict,
    remote_specs: dict,
    dry_run: bool = False,
    prefer: Optional[str] = None,
    tests_dir: Path = TESTS_DIR,
) -> None:
    """Synchronize local and remote specs."""
    all_files = set(local_specs.keys()).union(remote_specs.keys())
    specs_to_upload = {}
    specs_to_save = {}

    for file_path in all_files:
        local = local_specs.get(file_path, [])
        remote = remote_specs.get(file_path, [])

        # Create maps of specs by ID for easier comparison
        local_by_id = {spec.metadata.id: spec for spec in local}
        remote_by_id = {
            spec["metadata"]["id"]: YamlSpec(
                spec["content"],
                SpecMetadata(
                    id=spec["metadata"]["id"],
                    last_modified=spec["metadata"]["last_modified"],
                ),
            )
            for spec in remote
        }

        # All unique spec IDs
        all_ids = set(local_by_id.keys()).union(remote_by_id.keys())

        file_specs_to_upload = []
        file_specs_to_save = []

        for spec_id in all_ids:
            local_spec = local_by_id.get(spec_id)
            remote_spec = remote_by_id.get(spec_id)

            if local_spec and not remote_spec:
                if not dry_run:
                    file_specs_to_upload.append(
                        {
                            "content": local_spec.data,
                            "metadata": {
                                "id": local_spec.metadata.id,
                                "last_modified": local_spec.metadata.last_modified,
                            },
                        }
                    )
                console.print(
                    f"[green]↑ Will upload new spec: {file_path} ({spec_id})[/green]"
                )

            elif not local_spec and remote_spec:
                if not dry_run:
                    file_specs_to_save.append(remote_spec)
                console.print(
                    f"[blue]↓ Will download new spec: {file_path} ({spec_id})[/blue]"
                )

            elif local_spec and remote_spec:
                local_time = datetime.fromisoformat(local_spec.metadata.last_modified)
                remote_time = datetime.fromisoformat(remote_spec.metadata.last_modified)

                if local_time != remote_time:
                    # Determine which version to keep
                    use_local = True
                    if prefer == "remote":
                        use_local = False
                    elif prefer == "local":
                        use_local = True
                    else:
                        use_local = local_time > remote_time

                    if use_local:
                        if not dry_run:
                            file_specs_to_upload.append(
                                {
                                    "content": local_spec.data,
                                    "metadata": {
                                        "id": local_spec.metadata.id,
                                        "last_modified": local_spec.metadata.last_modified,
                                    },
                                }
                            )
                        console.print(
                            f"[green]↑ Will update remote spec (local is newer): {file_path} ({spec_id})[/green]"
                        )
                    else:
                        if not dry_run:
                            file_specs_to_save.append(remote_spec)
                        console.print(
                            f"[blue]↓ Will update local spec (remote is newer): {file_path} ({spec_id})[/blue]"
                        )

        if file_specs_to_upload:
            specs_to_upload[file_path] = file_specs_to_upload
        if file_specs_to_save:
            specs_to_save[file_path] = file_specs_to_save

    # Perform all remote operations in a single call
    if not dry_run:
        if specs_to_upload:
            specs_service.upload_specs(branch, specs_to_upload)

        # Save all local changes
        for file_path, specs in specs_to_save.items():
            full_path = tests_dir / file_path
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            existing_specs = load_yaml_specs(full_path) if full_path.exists() else []
            # Remove specs that will be updated
            existing_specs = [
                s
                for s in existing_specs
                if s.metadata.id not in {spec.metadata.id for spec in specs}
            ]
            # Add new/updated specs
            existing_specs.extend(specs)
            save_yaml_specs(full_path, existing_specs)


@require_api_key
def sync_command(
    branch: Optional[str] = typer.Option(
        None, help="Branch to sync with (defaults to current git branch or 'main')"
    ),
    pull: bool = typer.Option(False, help="Only pull specs from remote"),
    push: bool = typer.Option(False, help="Only push specs to remote"),
    clean_remote: bool = typer.Option(
        False, help="Delete remote specs that don't exist locally"
    ),
    dry_run: bool = typer.Option(
        False, help="Show what would happen without making changes"
    ),
    prefer: str = typer.Option(
        None,
        "--prefer",
        help="Prefer 'local' or 'remote' when resolving conflicts",
        click_type=click.Choice(["local", "remote"]),
    ),
):
    """Synchronize local and remote specs."""
    try:
        branch = branch or get_current_branch()
        specs_service = SpecsService()

        with Status("[yellow]Loading specs...[/yellow]", spinner="dots") as status:
            # Load local specs
            local_specs = {}
            if TESTS_DIR.exists():
                for file in TESTS_DIR.rglob("*.yaml"):
                    rel_path = file.relative_to(TESTS_DIR)
                    local_specs[str(rel_path)] = load_yaml_specs(file)

            # Load remote specs
            remote_specs = specs_service.get_remote_specs(branch)

            status.update("[green]Specs loaded successfully![/green]")

        # If neither pull nor push is specified, do both
        do_pull = pull or (not pull and not push)
        do_push = push or (not pull and not push)

        if do_pull and do_push:
            # When doing both pull and push, do a full sync
            console.print("\n[cyan]Synchronizing specs...[/cyan]")
            sync_specs(
                specs_service,
                branch,
                local_specs,
                remote_specs,
                dry_run=dry_run,
                prefer=prefer,
                tests_dir=TESTS_DIR,
            )
        else:
            if do_pull:
                console.print("\n[blue]Pulling specs from remote...[/blue]")
                sync_specs(
                    specs_service,
                    branch,
                    {},  # No local specs for pull
                    remote_specs,
                    dry_run=dry_run,
                    prefer=prefer,
                    tests_dir=TESTS_DIR,
                )

            if do_push:
                console.print("\n[green]Pushing specs to remote...[/green]")
                sync_specs(
                    specs_service,
                    branch,
                    local_specs,
                    {},  # No remote specs for push
                    dry_run=dry_run,
                    prefer=prefer,
                    tests_dir=TESTS_DIR,
                )

        if clean_remote and not dry_run:
            files_to_delete = set(remote_specs.keys()) - set(local_specs.keys())
            if files_to_delete:
                specs_service.delete_specs(branch, list(files_to_delete))
                console.print(
                    f"\n[yellow]Deleted {len(files_to_delete)} remote specs that don't exist locally[/yellow]"
                )

        # Final step: Ensure all local specs are saved with metadata
        if not dry_run and TESTS_DIR.exists():
            console.print("\n[cyan]Updating local files with metadata...[/cyan]")
            for file in TESTS_DIR.rglob("*.yaml"):
                try:
                    # Load specs (this will auto-generate metadata for specs that don't have it)
                    specs = load_yaml_specs(file)

                    # Check if any spec needs metadata update by comparing file content
                    with open(file, "r") as f:
                        original_content = f.read()

                    # Generate new content with metadata
                    new_content = "\n\n".join(spec.to_yaml() for spec in specs)

                    # Only write if content has changed (to avoid unnecessary file modifications)
                    if original_content.strip() != new_content.strip():
                        save_yaml_specs(file, specs)
                        rel_path = file.relative_to(TESTS_DIR)
                        console.print(
                            f"[cyan]  ✓ Updated metadata in {rel_path}[/cyan]"
                        )

                except Exception as e:
                    rel_path = file.relative_to(TESTS_DIR)
                    console.print(
                        f"[yellow]  ⚠ Warning: Could not update metadata in {rel_path}: {e}[/yellow]"
                    )

        console.print("\n[green]Sync completed successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
