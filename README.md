# Bugster CLI

![release version](https://img.shields.io/github/v/release/Bugsterapp/bugster-cli)
![build status](https://img.shields.io/github/workflow/status/Bugsterapp/bugster-cli/CI)

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

1. Download [install.bat](https://github.com/Bugsterapp/bugster-cli/releases/latest/download/install.bat)
2. Right-click and select "Run as administrator"

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
