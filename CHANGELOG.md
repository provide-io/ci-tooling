# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository structure
- Core GitHub Actions:
  - `setup-python-env`: Python, UV, and workenv setup
  - `python-quality`: Ruff linting and mypy type checking
  - `python-test`: Pytest execution with coverage
  - `python-security`: Security scanning with bandit, safety, pip-audit
  - `python-build`: Package building with UV
  - `python-release`: PyPI publishing and GitHub releases
- Reusable workflows:
  - `python-ci.yml`: Complete CI pipeline
  - `python-release.yml`: Release workflow
- Project templates for different use cases
- Migration scripts and documentation
- Comprehensive documentation

### Security
- SARIF report generation for security findings
- Integration with GitHub Security tab
- Configurable security thresholds

## [0.0.0] - 2025-01-16

### Added
- Initial release of provide.io CI tooling
- Repository structure established
- Core actions implemented
- Documentation framework created