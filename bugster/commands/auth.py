"""
Login command implementation for Bugster CLI.
"""

from rich.console import Console
from rich.prompt import Prompt
from bugster.analytics import track_command
from bugster.utils.user_config import save_api_key, get_api_key, load_user_config, save_user_config
from bugster.utils.console_messages import AuthMessages
import webbrowser
from typing import Optional

console = Console()

DASHBOARD_URL = "https://gui.bugster.dev/"  # Update this with your actual dashboard URL
API_KEY_HINT = "bugster_..."

def clear_api_key():
    """Remove the API key from the config file."""
    config = load_user_config()
    if "apiKey" in config:
        del config["apiKey"]
        save_user_config(config)
        return True
    return False

@track_command("auth")
def auth_command(api_key: Optional[str] = None, clear: bool = False):
    """Authenticate user with Bugster API key."""
    console.print()
    
    # Handle --clear flag
    if clear:
        existing_key = get_api_key()
        if existing_key:
            if clear_api_key():
                console.print("✅ [green]API key cleared successfully![/green]")
            else:
                console.print("❌ [red]Error clearing API key.[/red]")
        else:
            console.print("ℹ️  [yellow]No API key found to clear.[/yellow]")
        return
    
    # Clear existing API key before setting new one
    existing_key = get_api_key()
    if existing_key:
        console.print("🔄 [yellow]Removing existing API key...[/yellow]")
        clear_api_key()
    
    # Handle --api-key flag
    if api_key:
        # Validate provided API key
        if not api_key.strip():
            console.print("❌ [red]API key cannot be empty.[/red]")
            return
            
        if not api_key.startswith("bugster_"):
            console.print("⚠️  [yellow]Warning: API keys typically start with 'bugster_'[/yellow]")
            if Prompt.ask(
                "🤔 Continue anyway?",
                choices=["y", "n"],
                default="n"
            ) == "n":
                console.print("❌ [red]Authentication cancelled.[/red]")
                return
        
        console.print("🔄 [yellow]Validating API key...[/yellow]")
        
        if validate_api_key(api_key):
            try:
                save_api_key(api_key)
                console.print("✅ [green]API key saved successfully![/green]")
                        
            except Exception as e:
                console.print(f"❌ [red]Error saving API key: {str(e)}[/red]")
        else:
            console.print("❌ [red]Invalid API key. Please check and try again.[/red]")
        return
    
    # Interactive flow (original behavior)
    # Show authentication panel
    auth_panel = AuthMessages.create_auth_panel()
    console.print(auth_panel)
    console.print()
    
    # Option to open browser
    if Prompt.ask(
        AuthMessages.ask_open_dashboard(),
        choices=["y", "n"],
        default="y"
    ) == "y":
        AuthMessages.opening_dashboard()
        webbrowser.open(DASHBOARD_URL)
        console.print()
    
    # Get API key with validation
    while True:
        AuthMessages.api_key_prompt()
        user_api_key = Prompt.ask(AuthMessages.get_api_key_prompt()).strip()
        
        if not user_api_key:
            AuthMessages.empty_api_key_error()
            continue
            
        if not user_api_key.startswith("bugster_"):
            AuthMessages.invalid_prefix_warning()
            if Prompt.ask(
                AuthMessages.get_continue_anyway_prompt(),
                choices=["y", "n"],
                default="n"
            ) == "n":
                continue
        
        AuthMessages.validating_api_key()
        
        if validate_api_key(user_api_key):  
            break
        else:
            AuthMessages.invalid_api_key_error()
            continue
    
    # Save API key
    try:
        save_api_key(user_api_key)
        AuthMessages.auth_success()
    except Exception as e:
        AuthMessages.auth_error(e)
        raise

def validate_api_key(api_key: str) -> bool:
    """Validate API key by making a test request"""
    try:
        # Add actual API validation logic here
        # For now, just check format
        return len(api_key) > 10 and api_key.startswith("bugster_")
    except Exception:
        return False