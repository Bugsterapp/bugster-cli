# Bugster CLI

![release version](https://img.shields.io/github/v/release/Bugsterapp/bugster-cli?color=green)

🐛 **Bugster Agent - Simple Browser testing**

Bugster CLI generate comprehensive test specs for your web applications and keep them synchronized across your team. Minimal setup.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Configuration](#configuration)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Features

✨ **AI-Powered Test Generation**: Automatically analyze your codebase and generate comprehensive test specs  
🎯 **Intelligent Updates**: Automatically update test specs when your code changes  
🚀 **Cross-Platform**: Works on Windows, macOS, and Linux  
🌐 **Framework Support**: Currently supports Next.js applications  
📊 **Dashboard Integration**: Stream results to the Bugster dashboard for team visibility

## Installation

### Automated Installation (Recommended)

Our installers automatically check for and install dependencies (Node.js 18+, Playwright).

#### macOS/Linux

```bash
curl -sSL https://github.com/Bugsterapp/bugster-cli/releases/latest/download/install.sh | bash -s -- -y
```

#### Windows

##### Recommended Method (PowerShell)
The recommended way to install Bugster CLI on Windows is by using the PowerShell installer. Open a PowerShell terminal and run the following command:
```powershell
iwr https://raw.githubusercontent.com/Bugsterapp/bugster-cli/main/scripts/install.ps1 -useb | iex
```
This command downloads and executes the official installer script, which will:
1.  Determine the correct version for your system.
2.  Download the binary from the latest GitHub Release.
3.  Unzip and place it in a standard user directory (`%LOCALAPPDATA%\Programs\bugster`).
4.  Add the installation directory to your user's `PATH` environment variable.

After installation, you must **open a new terminal window** for the `bugster` command to be available.

##### Manual Installation

If you prefer not to run the script, you can install the CLI manually:
1.  Go to the [latest GitHub Release](https://github.com/Bugsterapp/bugster-cli/releases/latest).
2.  Download the `bugster-windows.zip` file.
3.  Extract the `bugster.exe` file to a directory of your choice (e.g., `C:\Program Files\bugster`).
4.  Manually add that directory to your system's or user's `PATH` environment variable.

##### Troubleshooting

###### 1. Antivirus / Windows Defender flags the executable

**Symptom:** After running the installer, `bugster.exe` is not found in the installation directory (`%LOCALAPPDATA%\Programs\bugster`), or it disappears shortly after installation.

**Cause:** Because the executable is downloaded from the internet and is not digitally signed by a major publisher, Windows Defender or other antivirus software may automatically quarantine or delete it as a security precaution.

**Solution:**
1.  Open **Windows Security** > **Virus & threat protection**.
2.  Go to **Protection history** to see if `bugster.exe` was quarantined. If so, you can restore it and allow it on your device.
3.  To prevent this from happening in the future, add an exclusion:
    *   Under **Virus & threat protection settings**, click **Manage settings**.
    *   Scroll down to **Exclusions** and click **Add or remove exclusions**.
    *   Click **Add an exclusion**, select **Folder**, and paste the following path: `%LOCALAPPDATA%\Programs\bugster`

###### 2. Command `bugster` not found after installation

**Symptom:** After a successful installation, you type `bugster --help` and get an error like `'bugster' is not recognized...`.

**Cause:** The terminal session where you ran the installer has an old copy of the `PATH` variable. The changes made by the installer will only be loaded by new terminal sessions.

**Solution:**
Close your current terminal window and **open a new one**. The command should now work correctly.

## Quick Start

1. **Initialize your project**

   ```bash
   bugster init
   ```

2. **Generate test cases**

   ```bash
   bugster generate
   ```

3. **Run your tests**

   ```bash
   bugster run
   ```

4. **Keep tests up to date**
   ```bash
   bugster update
   ```

## Commands

### `bugster init`

Initialize Bugster CLI configuration in your project. Sets up authentication, project settings, and test credentials.

```bash
bugster init
```

### `bugster generate`

Analyze your codebase and generate AI-powered test specs. This command scans your application structure and creates comprehensive test cases.

```bash
bugster generate [options]

Options:
  -f, --force        Force analysis even if already completed
  --show-logs        Show detailed logs during analysis
```

### `bugster run`

Execute your Bugster tests with various options for different environments.

```bash
bugster run [path] [options]

Arguments:
  path               Path to test file or directory (optional)

Options:
  --headless         Run tests in headless mode
  --silent           Run in silent mode (less verbose output)
  --stream-results   Stream test results to dashboard
  --output FILE      Save test results to JSON file
  --base-url URL     Override base URL for testing
  --only-affected    Only run tests affected by recent changes
  --max-concurrent N Maximum concurrent tests (up to 5)
  --verbose          Show detailed execution logs
```

**Examples:**

```bash
# Run all tests
bugster run

# Run tests in a specific directory
bugster run auth/

# Run with custom configuration
bugster run --headless --stream-results

# Run only tests affected by code changes
bugster run --only-affected
```

### `bugster update`

Update your test specs when your codebase changes. Intelligently detects modifications and updates relevant tests.

```bash
bugster update [options]

Options:
  --update-only      Only update existing specs
  --suggest-only     Only suggest new specs
  --delete-only      Only delete obsolete specs
  --show-logs        Show detailed logs during analysis
```

### `bugster sync`

Synchronize test cases with your team across different branches and environments.

```bash
bugster sync [options]

Options:
  --branch BRANCH    Branch to sync with (defaults to current)
  --pull             Only pull specs from remote
  --push             Only push specs to remote
  --clean-remote     Delete remote specs that don't exist locally
  --dry-run          Show what would happen without making changes
  --prefer OPTION    Prefer 'local' or 'remote' when resolving conflicts
```

**Examples:**

```bash
# Sync with main branch
bugster sync --branch main

# Only download remote changes
bugster sync --pull

# Preview sync changes
bugster sync --dry-run
```

### `bugster issues`

Get debugging information about failed test runs from recent executions.

```bash
bugster issues [options]

Options:
  --history          Get issues from the last week
  --save             Save issues to .bugster/issues directory
```

### `bugster upgrade`

Update Bugster CLI to the latest version.

```bash
bugster upgrade [options]

Options:
  -y, --yes          Automatically confirm the upgrade
```

## Configuration

Bugster CLI uses a YAML configuration file located at `.bugster/config.yaml`:

```yaml
project_name: "My App"
project_id: "my-app-123456"
base_url: "http://localhost:3000"
credentials:
  - id: "admin"
    username: "admin"
    password: "admin"
x-vercel-protection-bypass: "optional-bypass-key"
```

### Authentication

Set up your API key to connect with the Bugster platform:

```bash
bugster auth
```

This will guide you through:

1. Opening the Bugster dashboard
2. Copying your API key
3. Configuring authentication locally

## Examples

### Basic Workflow

```bash
# 1. Set up your project
bugster init

# 2. Generate test cases from your codebase
bugster generate

# 3. Run all tests
bugster run

# 4. Run specific tests with streaming
bugster run auth/ --stream-results
```

### CI/CD Integration

```bash
# Run tests in CI environment
bugster run \
  --headless \
  --stream-results \
  --base-url $PREVIEW_URL \
  --output results.json
```

### Team Collaboration

```bash
# Pull latest test changes from team
bugster sync --pull

# Update tests after code changes
bugster update

# Push updated tests to team
bugster sync --push
```

### Advanced Usage

```bash
# Run only tests affected by recent changes
bugster run --only-affected --max-concurrent 3

# Generate test cases with debugging
bugster generate --force --show-logs

# Sync with conflict resolution
bugster sync --prefer local --dry-run
```

## Project Structure

After initialization, Bugster creates the following structure:

```
.bugster/
├── config.yaml          # Project configuration
├── tests/               # Generated test specifications
│   ├── auth/           # Feature-based test organization
│   │   ├── 1_login.yaml
│   │   └── 2_signup.yaml
│   └── dashboard/
│       └── 1_overview.yaml
├── results/            # Test execution results
├── videos/             # Test recordings (when enabled)
└── logs/              # Execution logs
```

## Supported Frameworks

- ✅ **Next.js**: Full support for both App Router and Pages Router
- 🚧 **React**: Coming soon
- 🚧 **Vue.js**: Coming soon

## Test Limits

Bugster CLI applies intelligent test limits to ensure efficient execution:

- **Free tier**: Up to 5 tests per execution
- **Distribution**: Tests are distributed across feature folders
- **Selection**: Representative tests are chosen using smart algorithms

## Requirements

- **Node.js**: 18 or higher
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Browser**: Chrome/Chromium (automatically installed via Playwright)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📚 **Documentation**: [docs.bugster.dev](https://docs.bugster.dev)
- 🌐 **Dashboard**: [app.bugster.dev](https://app.bugster.dev)
- 🐙 **GitHub**: [github.com/Bugsterapp/bugster-cli](https://github.com/Bugsterapp/bugster-cli)
- 💬 **Issues**: [GitHub Issues](https://github.com/Bugsterapp/bugster-cli/issues)

---

<div align="center">
  <p>Built with ❤️ by Bugster</p>
  <p>
    <a href="https://app.bugster.dev">Dashboard</a> •
    <a href="https://docs.bugster.dev">Documentation</a> •
    <a href="https://github.com/Bugsterapp/bugster-cli">GitHub</a>
  </p>
</div>
