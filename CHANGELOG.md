# Changelog

All notable changes to Bugster CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.7] - 2025-06-19

### Added
- Enhanced `bugster generate` specs generation capacity up to 20 specs for comprehensive coverage

### Changed
- Improved specs generation algorithm for better coverage and more realistic test scenarios


## [0.3.6] - 2025-06-19

### Added
- `bugster issues` command to get failed runs with debugging context from recent executions
- `bugster upgrade` command to update CLI to the latest version directly from the command line

### Changed
- Improved specs generation algorithm for better coverage and more realistic test scenarios

### Fixed
- Small bug of the console message during `bugster init`

## [0.3.0] - 2025-06-13

### Added
- `--only-affected` flag for `bugster run` to execute only specs affected by code changes
- `--max-concurrent` flag for `bugster run` supporting up to 5 parallel test executions
- Component-level tracking for `bugster update` command
- GitHub integration for running specs on Vercel preview deployments
- Cross-platform installer scripts for Windows, macOS, and Linux with automatic dependency management



### Changed
- Enhanced `bugster update` command now works at component granularity instead of file level
- Improved parallel test execution with better resource management
- Optimized change detection algorithm for more accurate affected test identification
- Rich console output with color-coded messages and progress indicators
- Enhanced error handling with detailed debugging information

### Fixed
- Performance improvements for large codebases with many components
- Better handling of component dependency tracking
- Reduced false positives in change detection

## [0.2.0] - 2025-06-06

### Added
- `bugster sync` command to retrieve and manage test specs across different branches
- `bugster auth` command for secure API key management with GUI integration
- `bugster update` command to automatically update test specs when codebase changes
- Project creation integration with Bugster GUI dashboard for execution tracking
- Branch-based specs synchronization

### Changed
- Enhanced `bugster init` command now creates projects in the GUI dashboard

### Fixed
- Authentication improvements
- Project initialization reliability
- Cross-branch synchronization edge cases

## [0.1.0] - 2025-05-21

### Added
- Initial CLI commands: `bugster init`, `bugster generate`, and `bugster run`
- Next.js application support with automatic framework detection
- Test specs generation (up to 5 test specs per application)
- Basic test execution engine with browser automation
- Project configuration system with YAML-based config files
- Core specs format and parsing capabilities

[Unreleased]: https://github.com/Bugsterapp/bugster-cli/compare/v0.3.7...HEAD
[0.3.7]: https://github.com/Bugsterapp/bugster-cli/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/Bugsterapp/bugster-cli/compare/v0.3.0...v0.3.6
[0.3.0]: https://github.com/Bugsterapp/bugster-cli/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Bugsterapp/bugster-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Bugsterapp/bugster-cli/releases/tag/v0.1.0