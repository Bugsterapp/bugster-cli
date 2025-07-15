#!/bin/bash
# Bugster CLI installer wrapper for Unix systems (macOS/Linux)

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
Bugster CLI Installer

This installer will automatically install:
- Python 3.10+ (installs Python 3.12 if needed)
- Node.js 18+ (installs Node.js 18 if needed)
- Bugster CLI

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

# Function to find best Python version
find_best_python() {
    for py_cmd in python3.12 python3.11 python3.10 python3 python; do
        if command -v "$py_cmd" &>/dev/null; then
            version=$($py_cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
            # Parse major and minor version numbers
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            # Check if version >= 3.10
            if [[ $major -gt 3 ]] || [[ $major -eq 3 && $minor -ge 10 ]]; then
                echo "$py_cmd"
                return 0
            fi
        fi
    done
    return 1
}

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

# Function to update shell config
update_shell_config() {
    local config_file="$1"
    local shell_type="$2"
    local arch_type="$3"
    local python_path="$4"
    
    # Create backup
    cp "$config_file" "${config_file}.bak"
    
    # Add Python configuration
    cat << EOF >> "$config_file"

# Bugster CLI Python configuration
if [ -d "$python_path" ]; then
    export PATH="$python_path:\$PATH"
    alias python="python3.12"
    alias python3="python3.12"
    alias pip="python3.12 -m pip"
    alias pip3="python3.12 -m pip"
fi
EOF
    
    if [[ "$OS" == "macOS" ]]; then
        # Add Homebrew paths based on architecture
        if [[ "$arch_type" == "arm64" ]]; then
            echo 'export PATH="/opt/homebrew/bin:$PATH"' >> "$config_file"
        else
            echo 'export PATH="/usr/local/bin:$PATH"' >> "$config_file"
        fi
    fi
    
    print_success "✅ Updated shell configuration in $config_file"
    print_warning "Please run 'source $config_file' to apply changes"
}

install_python_macos() {
    print_step "Installing Python 3.12 on macOS..."
    
    # Detect architecture
    local arch_type
    arch_type=$(uname -m)
    
    # Check if Homebrew is installed
    if ! command -v brew &>/dev/null; then
        print_step "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH temporarily
        if [[ "$arch_type" == "arm64" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    
    print_step "Installing Python 3.12 via Homebrew..."
    brew install python@3.12
    
    # Get Python installation path
    local python_path
    if [[ "$arch_type" == "arm64" ]]; then
        python_path="/opt/homebrew/opt/python@3.12/bin"
    else
        python_path="/usr/local/opt/python@3.12/bin"
    fi
    
    # Update shell configuration
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
        *)
            config_file="$HOME/.profile"
            ;;
    esac
    
    update_shell_config "$config_file" "$shell_type" "$arch_type" "$python_path"
    
    # Verify Python installation
    if command -v python3.12 &>/dev/null; then
        print_success "✅ Python 3.12 installed successfully!"
    else
        print_error "❌ Python 3.12 installation failed"
        exit 1
    fi
}

install_python_linux() {
    print_step "Installing Python 3.12 on Linux..."
    
    local python_path="/usr/local/bin"
    local install_cmd=""
    local pkg_manager=""
    
    # Detect package manager and prepare installation command
    if command -v apt-get &>/dev/null; then
        pkg_manager="apt"
        install_cmd="sudo apt-get update && sudo apt-get install -y software-properties-common && sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt-get install -y python3.12 python3.12-venv python3.12-distutils"
    elif command -v dnf &>/dev/null; then
        pkg_manager="dnf"
        install_cmd="sudo dnf install -y python3.12 python3.12-pip"
    elif command -v yum &>/dev/null; then
        pkg_manager="yum"
        install_cmd="sudo yum install -y epel-release && sudo yum install -y python3.12"
    elif command -v pacman &>/dev/null; then
        pkg_manager="pacman"
        install_cmd="sudo pacman -Sy --noconfirm python python-pip"
    elif command -v zypper &>/dev/null; then
        pkg_manager="zypper"
        install_cmd="sudo zypper install -y python312 python312-pip"
    else
        print_error "❌ Unsupported package manager. Please install Python 3.12 manually."
        exit 1
    fi
    
    print_step "Using $pkg_manager to install Python 3.12..."
    eval "$install_cmd"
    
    # Set up alternatives system
    if [[ "$pkg_manager" == "apt" || "$pkg_manager" == "yum" || "$pkg_manager" == "dnf" || "$pkg_manager" == "zypper" ]]; then
        sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1
        sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
        sudo update-alternatives --set python /usr/bin/python3.12
        sudo update-alternatives --set python3 /usr/bin/python3.12
    fi
    
    # Update shell configuration
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
        *)
            config_file="$HOME/.profile"
            ;;
    esac
    
    update_shell_config "$config_file" "$shell_type" "" "$python_path"
    
    # Verify Python installation
    if command -v python3.12 &>/dev/null; then
        print_success "✅ Python 3.12 installed successfully!"
    else
        print_error "❌ Python 3.12 installation failed"
        exit 1
    fi
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

# Check for Python version and install if needed
check_python_version() {
    local version=$1
    if [[ $version =~ ^Python\ 3\.([0-9]+) ]]; then
        local minor=${BASH_REMATCH[1]}
        if (( minor >= 10 )); then
            return 0
        fi
    fi
    return 1
}

# Check for Node.js version and install if needed
print_step "Checking Node.js installation..."
if check_node_version; then
    node_version=$(node --version)
    print_success "✅ Node.js $node_version is installed and meets requirements"
else
    if command -v node &>/dev/null; then
        node_version=$(node --version)
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

# Find best available Python version
best_python=$(find_best_python)
if [[ -n "$best_python" ]]; then
    version=$($best_python --version 2>&1)
    if check_python_version "$version"; then
        print_success "✅ Python $version is installed, continuing with installation..."
    else
        print_error "❌ Python 3.10 or higher is required (found $version)"
        if [[ "$AUTO_YES" == "true" ]]; then
            choice="y"
        else
            print_warning "Would you like to install Python 3.12? (y/n)"
            read -r choice
        fi
        if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
            if [[ "$OS" == "macOS" ]]; then
                install_python_macos
            else
                install_python_linux
            fi
        else
            print_error "Please install Python 3.10 or higher manually and try again."
            exit 1
        fi
    fi
else
    print_error "❌ Python 3 is not installed or not in your PATH"
    if [[ "$AUTO_YES" == "true" ]]; then
        choice="y"
    else
        print_warning "Would you like to install Python 3.12? (y/n)"
        read -r choice
    fi
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        if [[ "$OS" == "macOS" ]]; then
            install_python_macos
        else
            install_python_linux
        fi
    else
        print_error "Please install Python 3.10 or higher manually and try again."
        exit 1
    fi
fi

print_step "Installing Playwright..."
CI=true npx -y playwright@1.53.0 install --with-deps chromium > /dev/null 2>&1
npx -y @playwright/mcp@latest --version
# Download and run the Python installer script with version argument
print_step "Downloading the Bugster CLI installer..."

# Find the best available Python executable
PYTHON_PATH=$(find_best_python)
if [[ -z "$PYTHON_PATH" ]]; then
    print_error "❌ No suitable Python version found. Please install Python 3.10 or higher."
    exit 1
fi

print_step "Using Python: $PYTHON_PATH"

if [[ "$VERSION" == "latest" ]]; then
    curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.py | "$PYTHON_PATH"
else
    curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.py | "$PYTHON_PATH" - -v "$VERSION"
fi

exit_code=$?
if [[ $exit_code -ne 0 ]]; then
    print_error "❌ Installation failed"
    exit $exit_code
fi

exit $exit_code 