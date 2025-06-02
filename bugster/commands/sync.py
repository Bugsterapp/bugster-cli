"""
Sync command implementation.
"""

from pathlib import Path
from typing import Dict, Optional, List
import typer
from rich.console import Console
from rich.status import Status
import subprocess
from datetime import datetime, timezone

from bugster.libs.services.specs_service import SyncService
from bugster.commands.middleware import require_api_key
from bugster.utils.yaml_spec import (
    load_spec,
    save_spec,
    YamlTestcase,
    TestCaseMetadata,
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
    sync_service: SyncService,
    branch: str,
    local_specs: Dict[str, List[YamlTestcase]],
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
            spec["metadata"]["id"]: YamlTestcase(
                spec["content"],
                TestCaseMetadata(
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
                    f"[green]↑ Will upload new test case: {file_path} ({spec_id})[/green]"
                )

            elif not local_spec and remote_spec:
                if not dry_run:
                    file_specs_to_save.append(remote_spec)
                console.print(
                    f"[blue]↓ Will download new test case: {file_path} ({spec_id})[/blue]"
                )

            elif local_spec and remote_spec:
                # First check if the content is actually different
                if local_spec.data == remote_spec.data:
                    # Content is the same, no sync needed
                    console.print(
                        f"[dim]  No changes needed for test case: {file_path} ({spec_id})[/dim]"
                    )
                    continue

                # Content is different, now check timestamps to resolve conflict
                local_time = datetime.fromisoformat(local_spec.metadata.last_modified)
                remote_time = datetime.fromisoformat(remote_spec.metadata.last_modified)

                # Determine which version to keep
                use_local = True
                if prefer == "remote":
                    use_local = False
                elif prefer == "local":
                    use_local = True
                else:
                    # If timestamps are equal, prefer local and update timestamp
                    if local_time == remote_time:
                        use_local = True
                        # Update local spec's timestamp to now
                        local_spec.metadata.last_modified = datetime.now(
                            timezone.utc
                        ).isoformat()
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
                        # If we updated the timestamp, also save the local spec to persist the change
                        if local_time == remote_time:
                            file_specs_to_save.append(local_spec)
                    reason = (
                        "local is newer"
                        if local_time > remote_time
                        else "preferring local with updated timestamp"
                    )
                    console.print(
                        f"[green]↑ Will update remote spec ({reason}): {file_path} ({spec_id})[/green]"
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
            sync_service.upload_test_cases(branch, specs_to_upload)

        # Save all local changes
        for file_path, specs in specs_to_save.items():
            full_path = tests_dir / file_path
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            existing_specs = load_spec(full_path) if full_path.exists() else []
            # Remove specs that will be updated
            existing_specs = [
                s
                for s in existing_specs
                if s.metadata.id not in {spec.metadata.id for spec in specs}
            ]
            # Add new/updated specs
            existing_specs.extend(specs)
            save_spec(full_path, existing_specs)


@require_api_key
def sync_command(
    branch: Optional[str] = None,
    pull: bool = False,
    push: bool = False,
    clean_remote: bool = False,
    dry_run: bool = False,
    prefer: Optional[str] = None,
) -> None:
    """Synchronize local and remote specs."""
    try:
        branch = branch or get_current_branch()
        sync_service = SyncService()

        with Status("[yellow]Loading specs...[/yellow]", spinner="dots") as status:
            # Load local specs
            local_specs = {}
            if TESTS_DIR.exists():
                for file in TESTS_DIR.rglob("*.yaml"):
                    rel_path = file.relative_to(TESTS_DIR)
                    local_specs[str(rel_path)] = load_spec(file)

            # Load remote specs
            remote_specs = sync_service.get_remote_test_cases(branch)

            status.update("[green]Specs loaded successfully![/green]")

        # Keep track of specs that were processed during sync to maintain metadata consistency
        processed_specs = {}  # file_path -> {spec_id -> YamlTestcase}

        # If neither pull nor push is specified, do both
        do_pull = pull or (not pull and not push)
        do_push = push or (not pull and not push)

        if clean_remote:
            # First identify files that don't exist locally at all (will be deleted entirely)
            files_to_delete = set(remote_specs.keys()) - set(local_specs.keys())

            # Find individual specs that exist in remote but not in local (only in files that exist locally)
            test_cases_to_delete = {}
            for file_path, remote_file_test_cases in remote_specs.items():
                # Skip files that will be deleted entirely
                if file_path in files_to_delete:
                    continue

                local_file_test_cases = local_specs.get(file_path, [])
                local_test_case_ids = {
                    test_case.metadata.id for test_case in local_file_test_cases
                }

                # Find remote specs that don't exist locally
                remote_test_cases_to_delete = [
                    test_case
                    for test_case in remote_file_test_cases
                    if test_case["metadata"]["id"] not in local_test_case_ids
                ]

                if remote_test_cases_to_delete:
                    test_cases_to_delete[file_path] = [
                        test_case["metadata"]["id"]
                        for test_case in remote_test_cases_to_delete
                    ]
                    for test_case in remote_test_cases_to_delete:
                        console.print(
                            f"[yellow]Will delete remote test case: {file_path} ({test_case['metadata']['id']})[/yellow]"
                        )

            # Show files that will be deleted entirely
            if files_to_delete:
                for file_path in files_to_delete:
                    console.print(
                        f"[yellow]Will delete entire remote file: {file_path}[/yellow]"
                    )

            if not dry_run:
                if test_cases_to_delete:
                    sync_service.delete_specific_test_cases(
                        branch, test_cases_to_delete
                    )
                if files_to_delete:
                    sync_service.delete_specs(branch, list(files_to_delete))

                total_deleted_test_cases = sum(
                    len(test_case_ids)
                    for test_case_ids in test_cases_to_delete.values()
                )
                if total_deleted_test_cases > 0 or files_to_delete:
                    console.print(
                        f"\n[yellow]Deleted {total_deleted_test_cases} test cases and {len(files_to_delete)} complete files from remote[/yellow]"
                    )

        elif do_pull and do_push:
            # When doing both pull and push, do a full sync
            console.print("\n[cyan]Synchronizing specs...[/cyan]")
            sync_specs(
                sync_service,
                branch,
                local_specs,
                remote_specs,
                dry_run=dry_run,
                prefer=prefer,
                tests_dir=TESTS_DIR,
            )
            # Track processed test cases
            for file_path, test_cases in local_specs.items():
                processed_specs[file_path] = {
                    test_case.metadata.id: test_case for test_case in test_cases
                }
        else:
            if do_pull:
                console.print("\n[blue]Pulling specs from remote...[/blue]")
                sync_specs(
                    sync_service,
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
                    sync_service,
                    branch,
                    local_specs,
                    {},  # No remote specs for push
                    dry_run=dry_run,
                    prefer=prefer,
                    tests_dir=TESTS_DIR,
                )
                # Track processed test cases for push
                for file_path, test_cases in local_specs.items():
                    processed_specs[file_path] = {
                        test_case.metadata.id: test_case for test_case in test_cases
                    }

        # Final step: Ensure all local test cases are saved with metadata
        if not dry_run and TESTS_DIR.exists():
            console.print("\n[cyan]Updating local files with metadata...[/cyan]")
            for file in TESTS_DIR.rglob("*.yaml"):
                try:
                    rel_path = str(file.relative_to(TESTS_DIR))

                    # Load test cases (this will auto-generate metadata for test cases that don't have it)
                    test_cases = load_spec(file)

                    # If we have processed test cases for this file, use their metadata to maintain consistency
                    if rel_path in processed_specs:
                        processed_specs_by_content = {}
                        for test_case_id, processed_test_case in processed_specs[
                            rel_path
                        ].items():
                            # Create a key based on test case content to match with loaded test cases
                            content_key = str(processed_test_case.data)
                            processed_specs_by_content[content_key] = (
                                processed_test_case
                            )

                        # Update loaded specs with processed metadata where content matches
                        for test_case in test_cases:
                            content_key = str(test_case.data)
                            if content_key in processed_specs_by_content:
                                # Use the metadata from the processed spec to maintain consistency
                                test_case.metadata = processed_specs_by_content[
                                    content_key
                                ].metadata

                    # Check if any spec needs metadata update by comparing file content
                    with open(file, "r") as f:
                        original_content = f.read()

                    # Generate new content with metadata
                    new_content = "\n\n".join(
                        test_case.to_yaml() for test_case in test_cases
                    )

                    # Only write if content has changed (to avoid unnecessary file modifications)
                    if original_content.strip() != new_content.strip():
                        save_spec(file, test_cases)
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
