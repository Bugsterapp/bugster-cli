#!/bin/bash
# Bugster CLI installer for Unix systems (macOS/Linux) - No Python Required
# Combines functionality of install.sh + install.py for compiled binaries

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Constants
GITHUB_REPO="https://github.com/Bugsterapp/bugster-cli"
GITHUB_API="https://api.github.com/repos/Bugsterapp/bugster-cli"
# TODO: keep this automatically synced with the last bugster version
DEFAULT_VERSION="v0.3.25"

# Print functions
print_step() {
    echo -e "\n${BLUE}=> $1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

# Help message
show_help() {
    cat << EOF
Bugster CLI Installer (No Python Required)

This installer will automatically install:
- Node.js 18+ (installs Node.js 18 if needed)
- Bugster CLI (compiled binary)

Usage: 
    ./install.sh [options]
    curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.sh | bash -s -- [options]

Options:
    -v, --version VERSION    Install specific version (e.g., v0.2.8, v0.2.8-beta.1)
    -h, --help              Show this help message
    -y, --yes              Automatic yes to prompts

Examples:
    ./install.sh                           # Install latest version
    ./install.sh -v v0.2.8                # Install specific version
    ./install.sh -v v0.2.8-beta.1         # Install beta version
    ./install.sh -y                       # Install with automatic yes to prompts
EOF
}

# Parse command line arguments
VERSION="latest"
AUTO_YES=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -y|--yes)
            AUTO_YES=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_step "Detected operating system: $OS"

# Function to check Node.js version
check_node_version() {
    if command -v node &>/dev/null; then
        local node_version=$(node --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        local major_version=$(echo "$node_version" | cut -d. -f1)
        if [[ "$major_version" -ge 18 ]]; then
            return 0
        fi
    fi
    return 1
}

# Function to install Node.js on macOS
install_node_macos() {
    print_step "Installing Node.js 18 on macOS..."
    
    # Check if Homebrew is installed
    if ! command -v brew &>/dev/null; then
        print_step "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH temporarily
        local arch_type=$(uname -m)
        if [[ "$arch_type" == "arm64" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    
    print_step "Installing Node.js 18 via Homebrew..."
    brew install node@18
    
    # Link Node.js 18
    brew link --force node@18
    
    # Verify Node.js installation
    if command -v node &>/dev/null && check_node_version; then
        print_success "✅ Node.js 18 installed successfully!"
    else
        print_error "❌ Node.js 18 installation failed"
        exit 1
    fi
}

# Function to install Node.js on Linux
install_node_linux() {
    print_step "Installing Node.js 18 on Linux..."
    
    local install_cmd=""
    local pkg_manager=""
    
    # Detect package manager and prepare installation command
    if command -v apt-get &>/dev/null; then
        pkg_manager="apt"
        print_step "Setting up NodeSource repository for Debian/Ubuntu..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        install_cmd="sudo apt-get install -y nodejs"
    elif command -v dnf &>/dev/null; then
        pkg_manager="dnf"
        print_step "Setting up NodeSource repository for RHEL/Fedora..."
        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
        install_cmd="sudo dnf install -y nodejs npm"
    elif command -v yum &>/dev/null; then
        pkg_manager="yum"
        print_step "Setting up NodeSource repository for CentOS/RHEL..."
        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
        install_cmd="sudo yum install -y nodejs npm"
    elif command -v pacman &>/dev/null; then
        pkg_manager="pacman"
        print_step "Installing Node.js via pacman (Arch Linux)..."
        install_cmd="sudo pacman -Sy --noconfirm nodejs npm"
    elif command -v zypper &>/dev/null; then
        pkg_manager="zypper"
        print_step "Installing Node.js via zypper (openSUSE)..."
        install_cmd="sudo zypper install -y nodejs18 npm18"
    else
        print_error "❌ Unsupported package manager. Please install Node.js 18 manually."
        print_warning "Visit https://nodejs.org/en/download/ for manual installation instructions."
        exit 1
    fi
    
    print_step "Using $pkg_manager to install Node.js 18..."
    eval "$install_cmd"
    
    # Verify Node.js installation
    if command -v node &>/dev/null && check_node_version; then
        print_success "✅ Node.js 18 installed successfully!"
    else
        print_error "❌ Node.js 18 installation failed"
        print_warning "Please install Node.js 18 manually from https://nodejs.org/"
        exit 1
    fi
}

# Function to validate version format
validate_version() {
    local version="$1"
    if [[ "$version" == "latest" ]]; then
        return 0
    fi
    if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-beta\.[0-9]+|-rc\.[0-9]+|-alpha\.[0-9]+)?$ ]]; then
        print_error "Invalid version format. Examples of valid versions:"
        print_error "  - v0.2.8"
        print_error "  - v0.2.8-beta.1"
        print_error "  - v0.2.8-rc.1"
        print_error "  - v0.2.8-alpha.1"
        print_error "  - latest"
        return 1
    fi
    return 0
}

# Function to get latest version from GitHub
get_latest_version() {
    local latest_version
    latest_version=$(curl -s "${GITHUB_API}/releases/latest" | grep '"tag_name"' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    
    if [[ -n "$latest_version" ]]; then
        echo "$latest_version"
    else
        echo "$DEFAULT_VERSION"
    fi
}

# Function to check if version exists
check_version_exists() {
    local version="$1"
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "${GITHUB_API}/releases/tags/${version}")
    if [[ "$status_code" == "200" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to detect platform and architecture
detect_platform() {
    local system="$1"
    local machine=$(uname -m)
    
    if [[ "$system" == "macOS" ]]; then
        if [[ "$machine" == "x86_64" || "$machine" == "amd64" ]]; then
            echo "bugster-macos-intel.zip"
        elif [[ "$machine" == "arm64" || "$machine" == "aarch64" ]]; then
            echo "bugster-macos-arm64.zip"
        else
            print_warning "Unknown macOS architecture: $machine, defaulting to Intel"
            echo "bugster-macos-intel.zip"
        fi
    elif [[ "$system" == "Linux" ]]; then
        echo "bugster-linux.zip"
    else
        print_error "Unsupported platform: $system"
        exit 1
    fi
}

# Function to download file with progress
download_with_progress() {
    local url="$1"
    local destination="$2"
    
    if command -v curl &>/dev/null; then
        curl -L --progress-bar "$url" -o "$destination"
        return $?
    elif command -v wget &>/dev/null; then
        wget --progress=bar "$url" -O "$destination"
        return $?
    else
        print_error "Neither curl nor wget is available"
        return 1
    fi
}

# Function to download and extract Bugster CLI
download_and_extract_to() {
    local version="$1"
    local temp_dir="$2"
    local asset_name
    asset_name=$(detect_platform "$OS")
    
    # Download the asset
    local zip_path="$temp_dir/bugster.zip"
    local download_url="${GITHUB_REPO}/releases/download/${version}/${asset_name}"
    
    if ! download_with_progress "$download_url" "$zip_path"; then
        return 1
    fi
    
    # Extract the zip file
    if ! unzip -q "$zip_path" -d "$temp_dir"; then
        return 1
    fi
    
    # Find the executable
    local exe_path="$temp_dir/bugster"
    
    if [[ ! -f "$exe_path" ]]; then
        return 1
    fi
    
    # Make executable
    chmod +x "$exe_path"
    
    # Write the path to a temp file instead of echoing
    echo "$exe_path" > "$temp_dir/exe_path"
    return 0
}

# Global variable for installed path
BUGSTER_INSTALLED_PATH=""

# Function to install executable
install_executable() {
    local executable_path="$1"
    local install_dir="$HOME/.local/bin"
    local target_path="$install_dir/bugster"
    
    # Create installation directory if it doesn't exist
    mkdir -p "$install_dir"
    
    # Copy executable to installation directory
    if cp "$executable_path" "$target_path"; then
        chmod +x "$target_path"
        BUGSTER_INSTALLED_PATH="$target_path"
        return 0
    else
        print_error "Error installing executable to $target_path"
        return 1
    fi
}

# Function to add directory to PATH
add_to_path() {
    local install_dir="$1"
    
    local shell_type="${SHELL##*/}"
    local config_file
    local home_dir="$HOME"
    
    # Determine which shell config file to update
    case "$shell_type" in
        zsh)
            if [[ -f "$home_dir/.zshrc" ]]; then
                config_file="$home_dir/.zshrc"
            else
                config_file="$home_dir/.zprofile"
            fi
            ;;
        bash)
            if [[ -f "$home_dir/.bash_profile" ]]; then
                config_file="$home_dir/.bash_profile"
            else
                config_file="$home_dir/.bashrc"
            fi
            ;;
        fish)
            config_file="$home_dir/.config/fish/config.fish"
            mkdir -p "$(dirname "$config_file")" 2>/dev/null
            ;;
        *)
            config_file="$home_dir/.profile"
            ;;
    esac
    
    # Check if PATH export already exists
    if [[ -f "$config_file" ]] && grep -q "$install_dir" "$config_file" 2>/dev/null; then
        echo "already_exists:$config_file"
        return 0
    fi
    
    # Add PATH export to config file - write directly without function calls
    cat >> "$config_file" << EOL

# Added by Bugster CLI installer
export PATH="\$PATH:$install_dir"
EOL
    
    echo "added:$config_file"
    return 0
}

# Function to test installation
test_installation() {
    local installed_path="$1"
    local version="$2"
    
    print_step "Testing installation..."
    
    # Test that binary exists and works
    if [[ -x "$installed_path" ]]; then
        # Run --version to show the installed version
        "$installed_path" --version
        return 0
    else
        print_error "❌ Installation test failed - binary not found or not executable at $installed_path"
        return 1
    fi
}

# Function to cleanup temporary files
cleanup() {
    local temp_dir="$1"
    if [[ -n "$temp_dir" && -d "$temp_dir" ]]; then
        rm -rf "$temp_dir"
    fi
}

# Main installation function
main() {
    print_step "Starting Bugster CLI installation..."
    
    # Validate version format
    if ! validate_version "$VERSION"; then
        exit 1
    fi
    
    # Get version to install
    local install_version="$VERSION"
    if [[ "$install_version" == "latest" ]]; then
        install_version=$(get_latest_version)
        if [[ "$install_version" == "$DEFAULT_VERSION" ]]; then
            print_warning "Could not fetch latest version, using default: $install_version"
        fi
    fi
    
    # Check if version exists
    if ! check_version_exists "$install_version"; then
        print_error "Version $install_version not found"
        exit 1
    fi
    
    print_step "Installing Bugster CLI $install_version"
    
    # Check for Node.js version and install if needed
    print_step "Checking Node.js installation..."
    if check_node_version; then
        # Node.js is OK, continue silently
        true
    else
        if command -v node &>/dev/null; then
            local node_version=$(node --version)
            print_error "❌ Node.js 18 or higher is required (found $node_version)"
        else
            print_error "❌ Node.js is not installed"
        fi
        
        if [[ "$AUTO_YES" == "true" ]]; then
            choice="y"
        else
            print_warning "Would you like to install Node.js 18? (y/n)"
            read -r choice
        fi
        
        if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
            if [[ "$OS" == "macOS" ]]; then
                install_node_macos
            else
                install_node_linux
            fi
        else
            print_error "Please install Node.js 18 or higher manually and try again."
            exit 1
        fi
    fi
    
    # Install Playwright
    print_step "Installing Playwright..."
    # TODO: Install the playwright version used in @playwright/mcp
    CI=true npx -y playwright@1.54.1 install --with-deps chromium >/dev/null 2>&1
    npx -y @playwright/mcp@latest --version >/dev/null 2>&1 || true
    
    # Download and extract Bugster CLI
    local temp_dir
    temp_dir=$(mktemp -d)
    
    print_step "Downloading Bugster CLI $install_version for $OS..."
    local asset_name
    asset_name=$(detect_platform "$OS")
    local download_url="${GITHUB_REPO}/releases/download/${install_version}/${asset_name}"
    print_step "Downloading from $download_url..."
    
    if ! download_and_extract_to "$install_version" "$temp_dir"; then
        print_error "Failed to download and extract Bugster CLI"
        print_error "Check if $asset_name exists for version $install_version"
        print_error "URL: $download_url"
        cleanup "$temp_dir"
        exit 1
    fi
    
    # Read the executable path from the temp file
    local executable_path
    if [[ -f "$temp_dir/exe_path" ]]; then
        executable_path=$(cat "$temp_dir/exe_path")
    else
        print_error "Failed to get executable path"
        cleanup "$temp_dir"
        exit 1
    fi
    
    # Install executable and add to PATH
    if ! install_executable "$executable_path"; then
        cleanup "$temp_dir"
        exit 1
    fi
    
    local install_dir
    install_dir=$(dirname "$BUGSTER_INSTALLED_PATH")
    local path_result
    path_result=$(add_to_path "$install_dir")
    
    # Only show PATH messages on error or if added for first time
    if [[ "$path_result" == added:* ]]; then
        local config_file="${path_result#added:}"
        print_success "✅ Added to PATH in $config_file"
    elif [[ ! "$path_result" == already_exists:* ]]; then
        print_warning "⚠️  Could not update PATH in shell config"
    fi
    
    # Test installation (skip if we're in an upgrade)
    if [[ -z "$BUGSTER_UPGRADE_IN_PROGRESS" ]]; then
        if ! test_installation "$BUGSTER_INSTALLED_PATH" "$install_version"; then
            cleanup "$temp_dir"
            exit 1
        fi
    else
        print_step "Skipping installation test during upgrade process."
    fi
    
    # Clean up
    cleanup "$temp_dir"
    
    # Update shell environment and finish
    local shell_type="${SHELL##*/}"
    local config_file
    case "$shell_type" in
        zsh)
            config_file="$HOME/.zshrc"
            ;;
        bash)
            if [[ -f "$HOME/.bash_profile" ]]; then
                config_file="$HOME/.bash_profile"
            else
                config_file="$HOME/.bashrc"
            fi
            ;;
        fish)
            config_file="$HOME/.config/fish/config.fish"
            ;;
        *)
            config_file="$HOME/.profile"
            ;;
    esac
    
    # Source the config file automatically to load new PATH
    if [[ -f "$config_file" ]]; then
        source "$config_file" 2>/dev/null || true
        print_success "\nBugster CLI is now ready to use! Try:"
        print_success "  bugster --help"
    else
        print_warning "\nPlease restart your terminal to use Bugster CLI, then run:"
        print_warning "  bugster --help"
    fi
}

# Run main function
main

exit $? 