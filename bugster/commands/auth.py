"""
Login command implementation for Bugster CLI.
"""

from rich.console import Console
from rich.prompt import Prompt, Confirm
from bugster.analytics import track_command, BugsterAnalytics
from bugster.utils.user_config import save_api_key
from bugster.utils.console_messages import AuthMessages
import webbrowser

console = Console()

DASHBOARD_URL = "https://gui.bugster.dev/"  # Update this with your actual dashboard URL
API_KEY_HINT = "bugster_..."

@track_command("auth")
def auth_command():
    """Authenticate user with Bugster API key."""
    console.print()
    
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
        api_key = Prompt.ask(AuthMessages.get_api_key_prompt()).strip()
        
        if not api_key:
            AuthMessages.empty_api_key_error()
            continue
            
        if not api_key.startswith("bugster_"):
            AuthMessages.invalid_prefix_warning()
            if Prompt.ask(
                AuthMessages.get_continue_anyway_prompt(),
                choices=["y", "n"],
                default="n"
            ) == "n":
                continue
        
        AuthMessages.validating_api_key()
        
        if validate_api_key(api_key):  
            break
        else:
            AuthMessages.invalid_api_key_error()
            continue
    
    # Save API key
    try:
        save_api_key(api_key)
        AuthMessages.auth_success()
    except Exception as e:
        AuthMessages.auth_error(e)
        raise

    # Analytics opt-in/opt-out prompt (only if not already opted out)
    if not BugsterAnalytics.is_opted_out():
        analytics_panel = AuthMessages.create_analytics_panel()
        console.print(analytics_panel)
        console.print()
        
        enable_analytics = Confirm.ask(
            f"🤔 Would you like to help improve Bugster by sharing anonymous usage analytics?", 
            default=True
        )
        
        if not enable_analytics:
            BugsterAnalytics.create_opt_out_file()
            AuthMessages.analytics_disabled()
        else:
            AuthMessages.analytics_enabled()
        console.print()

def validate_api_key(api_key: str) -> bool:
    """Validate API key by making a test request"""
    try:
        # Add actual API validation logic here
        # For now, just check format
        return len(api_key) > 10 and api_key.startswith("bugster_")
    except Exception:
        return False