# Bugster CLI

Command line interface for Bugster

## Installation

### Automated Installation (Recommended)

Our installers will check for Python 3.10+, Node.js 18+ and Playwright dependencies, automatically installing them if needed (with your permission).

#### macOS/Linux

```bash
curl -sSL https://github.com/Bugsterapp/bugster-cli/releases/latest/download/install.sh | bash -s -- -y
```

#### Windows

1. Download [install.bat](https://github.com/Bugsterapp/bugster-cli/releases/latest/download/install.bat)
2. Right-click the downloaded file and select "Run as administrator"

### Manual Installation

If you already have Python 3.10+, Node.js 18+ and Playwright installed:

```bash
curl -sSL https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.py | python3
```

## Usage

```bash
bugster --help
```

## Development

### Setup

```bash
pip install -e .
```

### Building

```bash
pyinstaller bugster.spec
```
