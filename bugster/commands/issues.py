"""
Issues command implementation.
"""

import json
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from bugster.commands.middleware import require_api_key
from bugster.clients.http_client import BugsterHTTPClient
from bugster.constants import BUGSTER_DIR, CONFIG_PATH
from bugster.utils.file import load_config

console = Console()

def save_issue_to_file(issue_data: dict, project_id: str):
    """Save issue data to a file in the .bugster/issues directory."""
    issues_dir = Path(BUGSTER_DIR) / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{issue_data['run_id']}_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = issues_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(issue_data, f, indent=2, default=str)
    
    return filepath

def save_issues_batch(issues, project_id):
    """Save all issues in a single file inside a timestamped directory."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    issues_dir = Path(BUGSTER_DIR) / f"issues_{timestamp}"
    issues_dir.mkdir(parents=True, exist_ok=True)
    issues_file = issues_dir / f"{project_id}.json"
    with open(issues_file, 'w') as f:
        json.dump(issues, f, indent=2, default=str)
    return issues_file

@require_api_key
def issues_command(
    history: bool = typer.Option(
        False,
        "--history",
        help="Get issues from the last week. If more than 10 issues are found, they will be saved to .bugster/issues directory"
    ),
    save: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save issues to .bugster/issues directory"
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--project-id",
        "-p",
        help="Project ID (defaults to the one from config.yaml)"
    )
):
    """Get and display issues. Use --history to get issues from the last week."""
    try:
        # Get project_id from config if not provided
        if project_id is None:
            config = load_config()
            project_id = config.project_id
            if not project_id:
                console.print("[red]No project ID found. Please run 'bugster init' first or provide a project ID with --project-id[/red]")
                raise typer.Exit(1)
        
        with BugsterHTTPClient() as client:
            if history:
                # Get issues from last week
                response = client.get(
                    "/api/v1/issues/history",
                    params={
                        "project_id": project_id,
                        "limit": "50"  # Pedimos más del límite para saber si hay que guardar
                    }
                )
                
                if not response or not response.get("issues"):
                    console.print(f"[yellow]No historical issues found for project {project_id}[/yellow]")
                    return
                
                issues = response["issues"]
                total_issues = len(issues)
                
                # If more than 10 issues, save them directly
                if total_issues > 10:
                    issues_file = save_issues_batch(issues, project_id)
                    console.print(f"[green]Found {total_issues} issues. All saved to {issues_file}[/green]")
                    return
                
                # If there are 10 or fewer, display in a table
                table = Table(title=f"Issues from Last Week (Total: {total_issues})")
                table.add_column("Test Name", style="cyan")
                table.add_column("Created At", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Test Reason", style="blue", no_wrap=False)
                
                for issue in issues:
                    # Get the first test case info
                    test_case = issue["test_cases"][0] if issue["test_cases"] else {}
                    test_name = test_case.get("name", "N/A")
                    reason = test_case.get("reason", "No reason provided")
                    status = test_case.get("result", "unknown")
                    
                    table.add_row(
                        test_name,
                        issue["created_at"].split("T")[0] if "T" in issue["created_at"] else issue["created_at"],
                        status,
                        reason
                    )
                
                console.print(table)
                
                # If save was requested, save as well
                if save:
                    issues_file = save_issues_batch(issues, project_id)
                    console.print(f"[green]Issues also saved to {issues_file}[/green]")
                
            else:
                # Get latest issue
                try:
                    response = client.get(
                        "/api/v1/issues",
                        params={"project_id": project_id}
                    )
                except Exception as e:
                    if "404" in str(e):
                        console.print(f"[yellow]No recent issues for project_id {project_id}[/yellow]")
                        return
                    raise
                
                if not response:
                    console.print(f"[yellow]No recent issues for project_id {project_id}[/yellow]")
                    return
                
                issue = response
                
                # Display issue
                table = Table(title=f"Latest Issue for Project {project_id}")
                table.add_column("Test Name", style="cyan")
                table.add_column("Created At", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Test Reason", style="blue", no_wrap=False)
                
                # Display all test cases from the issue
                for test_case in issue["test_cases"]:
                    test_name = test_case.get("name", "N/A")
                    reason = test_case.get("reason", "No reason provided")
                    status = test_case.get("result", "unknown")
                    
                    table.add_row(
                        test_name,
                        issue["created_at"].split("T")[0] if "T" in issue["created_at"] else issue["created_at"],
                        status,
                        reason
                    )
                
                console.print(table)
                
                if save:
                    filepath = save_issue_to_file(issue, project_id)
                    console.print(f"[green]Issue saved to {filepath}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@require_api_key
def issues_history_command(
    save: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save issues to .bugster/issues directory"
    ),
    project_id: Optional[str] = typer.Option(
        None,
        "--project-id",
        "-p",
        help="Project ID (defaults to the one from config.yaml)"
    )
):
    """Get and display issues from the last week."""
    try:
        # Get project_id from config if not provided
        if project_id is None:
            config = load_config()
            project_id = config.project_id
            if not project_id:
                console.print("[red]No project ID found. Please run 'bugster init' first or provide a project ID with --project-id[/red]")
                raise typer.Exit(1)
        
        with BugsterHTTPClient() as client:
            # Get issues from last week
            response = client.get(
                "/api/v1/issues/history",
                params={
                    "project_id": project_id,
                    "limit": "50"  # Pedimos más del límite para saber si hay que guardar
                }
            )
            
            if not response or not response.get("issues"):
                console.print(f"[yellow]No historical issues found for project {project_id}[/yellow]")
                return
            
            issues = response["issues"]
            total_issues = len(issues)
            
            # If more than 10 issues, save them directly
            if total_issues > 10:
                issues_file = save_issues_batch(issues, project_id)
                console.print(f"[green]Found {total_issues} issues. All saved to {issues_file}[/green]")
                return
            
            # If there are 10 or fewer, display in a table
            table = Table(title=f"Issues from Last Week (Total: {total_issues})")
            table.add_column("Test Name", style="cyan")
            table.add_column("Created At", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Test Reason", style="blue", no_wrap=False)
            
            for issue in issues:
                # Get the first test case info
                test_case = issue["test_cases"][0] if issue["test_cases"] else {}
                test_name = test_case.get("name", "N/A")
                reason = test_case.get("reason", "No reason provided")
                status = test_case.get("result", "unknown")
                
                table.add_row(
                    test_name,
                    issue["created_at"].split("T")[0] if "T" in issue["created_at"] else issue["created_at"],
                    status,
                    reason
                )
            
            console.print(table)
            
            # If save was requested, save as well
            if save:
                issues_file = save_issues_batch(issues, project_id)
                console.print(f"[green]Issues also saved to {issues_file}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1) 