# OpenAlgo API Documentation



---

# FILE: docs\prd\ci-cd-local-development.md

# CI/CD Local Development Guide

## Overview

This guide explains how to run the same checks locally that run in CI, ensuring your code passes before pushing.

## Prerequisites

- Python 3.12+
- Node.js 20+ (22 recommended)
- uv package manager (`pip install uv`)
- Git

---

## Quick Start

```bash
# One-time setup: Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all checks before committing
pre-commit run --all-files

# Run backend tests
uv run pytest test/ -v

# Run frontend tests
cd frontend && npm test
```

---

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit, catching issues early.

### Installation

```bash
# Install pre-commit tool
pip install pre-commit

# Install hooks for this repository
pre-commit install

# Verify installation
pre-commit --version
```

### What Runs on Commit

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| Ruff check | Python linting | Yes |
| Ruff format | Python formatting | Yes |
| Biome check | TypeScript/React linting | Yes |
| detect-secrets | Secrets detection | No |
| trailing-whitespace | Remove trailing whitespace | Yes |
| end-of-file-fixer | Ensure newline at EOF | Yes |
| check-yaml | Validate YAML syntax | No |
| check-json | Validate JSON syntax | No |
| check-added-large-files | Prevent >1MB files | No |

### Manual Execution

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Run on specific files
pre-commit run --files src/app.py

# Skip hooks (emergency only)
git commit --no-verify -m "message"
```

### Updating Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# Test updated hooks
pre-commit run --all-files
```

---

## Backend Development

### Python Linting with Ruff

Ruff is 10-100x faster than flake8+black combined.

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Check formatting
uv run ruff format --check .

# Auto-format
uv run ruff format .
```

### Running Tests

```bash
# Run all tests
uv run pytest test/ -v

# Run with timeout (matches CI)
uv run pytest test/ -v --timeout=60

# Run specific test file
uv run pytest test/test_broker.py -v

# Run single test
uv run pytest test/test_broker.py::test_function_name -v

# Run with coverage
uv run pytest test/ --cov

# Skip sandbox tests (require running app)
uv run pytest test/ -v --ignore=test/sandbox
```

### Security Scanning

```bash
# Bandit static analysis
uv run bandit -r . -x .venv,test,frontend,node_modules -ll

# pip-audit vulnerability check
uv run pip-audit
```

---

## Frontend Development

### TypeScript/React Linting with Biome

```bash
cd frontend

# Check for issues
npm run lint

# Auto-fix issues
npm run lint -- --write

# Full check (lint + format)
npm run check
```

### Running Tests

```bash
cd frontend

# Run unit tests (watch mode)
npm test

# Run once (CI mode)
npm run test:run

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run e2e

# Run E2E with UI
npm run e2e -- --ui

# Run specific E2E project
npm run e2e -- --project=chromium
```

### Building

```bash
cd frontend

# Development build
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

---

## Root CSS Development

For Jinja2 templates (not React frontend).

```bash
# From repository root (not frontend/)

# Development mode (watch for changes)
npm run dev

# Production build
npm run build

# NEVER edit static/css/main.css directly!
# Edit src/css/styles.css instead
```

---

## IDE Integration

### VS Code

**Recommended Extensions:**
- Python (Microsoft)
- Ruff (Astral Software)
- Biome (biomejs.biome)
- Tailwind CSS IntelliSense

**Settings (.vscode/settings.json):**
```json
{
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "[typescript][typescriptreact]": {
    "editor.defaultFormatter": "biomejs.biome"
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["test/"]
}
```

### PyCharm / WebStorm

1. **Ruff:** Settings > Tools > File Watchers > Add Ruff
2. **Biome:** Install Biome plugin from marketplace
3. **pytest:** Settings > Tools > Python Integrated Tools > pytest

---

## Common Issues

### Pre-commit hook fails

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Ruff not finding config

Ensure you're running from repository root where `pyproject.toml` exists.

### Frontend tests fail with module errors

```bash
cd frontend
rm -rf node_modules
npm ci
npm test
```

### E2E tests fail - browser not found

```bash
cd frontend
npx playwright install --with-deps
```

### Python import errors

```bash
# Sync dependencies
uv sync

# Verify Python version
uv run python --version  # Should be 3.12+
```

---

## CI Parity Checklist

Before pushing, verify locally:

- [ ] `pre-commit run --all-files` passes
- [ ] `uv run pytest test/ -v --ignore=test/sandbox` passes
- [ ] `cd frontend && npm run lint` passes
- [ ] `cd frontend && npm run build` succeeds
- [ ] `cd frontend && npm run test:run` passes
- [ ] `npm run build` (root CSS) succeeds

If all pass locally, CI should pass too.



---

# FILE: docs\prd\ci-cd-security.md

# CI/CD Security Scanning

## Overview

This document details the security scanning tools and configurations in the OpenAlgo CI/CD pipeline.

## Security Tools

### 1. Bandit - Python Static Analysis

**Purpose:** Detects common security issues in Python code.

**Configuration:**
```bash
uv run bandit -r . -x .venv,test,frontend,node_modules -ll -f txt
```

| Flag | Purpose |
|------|---------|
| `-r .` | Recursive scan from root |
| `-x` | Exclude directories |
| `-ll` | Low severity and above |
| `-f txt` | Output format |

**Common Findings:**

| Issue | Severity | Action |
|-------|----------|--------|
| B101: assert_used | Low | Ignore in tests |
| B311: random | Low | Use `secrets` for security |
| B602: subprocess_shell | Medium | Use shell=False |
| B608: sql_injection | High | Use parameterized queries |

**Suppressing False Positives:**
```python
# nosec B101 - Assert is appropriate here for test validation
assert result == expected  # nosec
```

### 2. pip-audit - Dependency Vulnerability Scan

**Purpose:** Checks Python dependencies against known vulnerabilities (PyPI advisory database).

**Configuration:**
```bash
uv run pip-audit
```

**Output Example:**
```
Name        Version  ID               Fix Versions
----------  -------  ---------------  ------------
requests    2.25.0   PYSEC-2021-123   2.25.1
```

**Handling Vulnerabilities:**

1. **Update the package:**
   ```bash
   uv add package@latest
   ```

2. **If no fix available, document exception:**
   - Evaluate risk based on how the package is used
   - Add to security exceptions log if acceptable

### 3. Trivy - Docker Image Scanning

**Purpose:** Scans Docker images for OS and application vulnerabilities.

**Configuration:**
```yaml
- uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'openalgo:ci'
    exit-code: '0'
    severity: 'CRITICAL,HIGH'
    format: 'table'
```

| Flag | Purpose |
|------|---------|
| `exit-code: '0'` | Don't fail build (informational) |
| `severity` | Only report CRITICAL and HIGH |
| `format: 'table'` | Human-readable output |

**Vulnerability Categories:**
- **OS packages:** Alpine/Debian vulnerabilities
- **Language packages:** Python packages in image
- **Misconfigurations:** Dockerfile best practices

### 4. detect-secrets - Secrets Detection

**Purpose:** Prevents accidental commit of API keys, passwords, and tokens.

**Configuration (`.pre-commit-config.yaml`):**
```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
      exclude: package-lock\.json|uv\.lock
```

**Generating Baseline:**
```bash
# Initial baseline generation
uv run detect-secrets scan --exclude-files 'package-lock\.json|uv\.lock' > .secrets.baseline

# After reviewing false positives, audit and mark:
uv run detect-secrets audit .secrets.baseline
```

**Common False Positives:**
- Test fixtures with fake tokens
- Documentation examples
- Lock file hashes

---

## Weekly Security Workflow

**File:** `.github/workflows/security.yml`

**Schedule:** Every Monday at 2 AM UTC

**Purpose:** Comprehensive security audit independent of CI, providing:
- SARIF reports for GitHub Security tab
- JSON reports for archival
- Detailed vulnerability information

### GitHub Security Tab Integration

Bandit results are uploaded to GitHub's Security tab via SARIF format:
1. Go to repository > Security > Code scanning alerts
2. Filter by tool: "bandit"
3. Review and triage findings

### Security Artifacts

| Artifact | Format | Retention | Purpose |
|----------|--------|-----------|---------|
| `bandit.sarif` | SARIF | 30 days | GitHub Security integration |
| `pip-audit.json` | JSON | 30 days | Dependency audit trail |

---

## Security Best Practices

### For Contributors

1. **Run pre-commit hooks locally:**
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```

2. **Never commit secrets:**
   - Use `.env` files (gitignored)
   - Use environment variables in CI

3. **Review Bandit findings:**
   - Fix HIGH severity issues
   - Document exceptions for false positives

### For Maintainers

1. **Review weekly security report:**
   - Check GitHub Actions > Security Scan workflow
   - Triage new findings

2. **Handle Dependabot PRs:**
   - Merge security updates promptly
   - Test before merging major updates

3. **Monitor Docker image:**
   - Review Trivy output in docker-build job
   - Update base image regularly

---

## Required Secrets

The following secrets must be configured in GitHub repository settings:

| Secret | Purpose | Required For |
|--------|---------|--------------|
| `DOCKERHUB_USERNAME` | Docker Hub login | docker-build job |
| `DOCKERHUB_TOKEN` | Docker Hub access token | docker-build job |
| `GITHUB_TOKEN` | Auto-provided by GitHub | SARIF upload, auto-commit |

**Setting up Docker Hub token:**
1. Go to Docker Hub > Account Settings > Security
2. Create Access Token with Read/Write permissions
3. Add to GitHub: Settings > Secrets > Actions > New secret

---

## Vulnerability Response Process

### Critical Vulnerabilities

1. **Immediate assessment:** Determine if vulnerability is exploitable in OpenAlgo context
2. **Patch or mitigate:** Update dependency or implement workaround
3. **Release:** Create patch release if in production

### High Vulnerabilities

1. **Triage within 7 days**
2. **Plan remediation** in next release cycle
3. **Document** if accepting risk

### Medium/Low Vulnerabilities

1. **Track** in issue tracker
2. **Address** during regular maintenance
3. **Batch** with other updates when possible



---

# FILE: docs\prd\ci-cd-workflows.md

# CI/CD Workflows Reference

## Overview

This document details all GitHub Actions workflows in the OpenAlgo CI/CD pipeline.

## Main CI Workflow

**File:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `main` branch
- Pull requests targeting `main` branch

**Concurrency:** Cancels in-progress runs when new commits are pushed to the same branch.

### Jobs Summary

| Job | Runtime | Purpose |
|-----|---------|---------|
| backend-lint | ~30s | Python code quality |
| backend-test | ~60s | Python unit tests |
| frontend-lint | ~30s | TypeScript/React linting |
| frontend-build | ~90s | Production build verification |
| frontend-test | ~45s | React unit tests |
| frontend-e2e | ~120s | Browser automation tests |
| security-scan | ~45s | Vulnerability detection |
| docker-build | ~180s | Container build + scan |
| root-css-build | ~30s | Tailwind CSS compilation |

**Total Runtime:** ~3-4 minutes (all jobs run in parallel)

---

## Job Details

### backend-lint

Validates Python code quality using Ruff (10-100x faster than flake8+black).

```yaml
steps:
  - uv sync --dev
  - uv run ruff check .        # Linting
  - uv run ruff format --check # Formatting
```

**Failure Reasons:**
- Syntax errors
- Import sorting issues
- Code style violations
- Unused imports/variables

**Fix Locally:**
```bash
uv run ruff check . --fix
uv run ruff format .
```

### backend-test

Runs a minimal CI-safe subset of Python tests that don't require broker credentials.

```yaml
steps:
  - uv sync
  - uv run pytest test/test_log_location.py test/test_navigation_update.py \
      test/test_python_editor.py test/test_rate_limits_simple.py \
      test/test_logout_csrf.py -v --timeout=60
```

**CI-Safe Tests:**
- `test_log_location.py` - Log file path validation
- `test_navigation_update.py` - Navigation structure tests
- `test_python_editor.py` - Editor functionality tests
- `test_rate_limits_simple.py` - Rate limiter configuration tests
- `test_logout_csrf.py` - CSRF protection tests

**Notes:**
- Only runs tests that don't need broker credentials or running app
- Full test suite available locally: `uv run pytest test/ -v`
- 60-second timeout per test

### frontend-lint

Validates TypeScript/React code using Biome.

```yaml
steps:
  - npm ci
  - npm run lint
```

**Fix Locally:**
```bash
cd frontend
npm run lint -- --write
# or
npm run check
```

### frontend-build

Builds the production React application.

```yaml
steps:
  - npm ci
  - npm run build  # Includes TypeScript check
```

**Artifacts:**
- `frontend-dist` - Built files (7-day retention)

**Failure Reasons:**
- TypeScript type errors
- Import resolution failures
- Build configuration issues

### frontend-test

Runs React unit tests with Vitest.

```yaml
steps:
  - npm ci
  - npm run test:run
  - npm run test:coverage
```

**Artifacts:**
- `coverage-report` - HTML coverage report (7-day retention)

### frontend-e2e

Runs Playwright browser automation tests.

```yaml
steps:
  - npm ci
  - npx playwright install --with-deps chromium
  - npm run e2e -- --project=chromium
```

**Notes:**
- Only runs Chromium for speed (full browser matrix runs locally)
- Uploads report on failure only

**Artifacts (on failure):**
- `playwright-report` - HTML test report

### security-scan

Scans for security vulnerabilities.

```yaml
steps:
  - uv run bandit -r . -x .venv,test,frontend,node_modules -ll
  - uv run pip-audit
```

**Notes:**
- `continue-on-error: true` - Findings are informational
- Results visible in job logs

### docker-build

Builds and scans the Docker image.

```yaml
steps:
  - docker/build-push-action (with GHA cache)
  - trivy scan for CRITICAL,HIGH vulnerabilities
```

**Caching:**
- Uses GitHub Actions cache (`type=gha`)
- Layer caching for fast rebuilds

### root-css-build

Builds the Tailwind CSS for Jinja templates.

```yaml
steps:
  - npm ci
  - npm run build  # PostCSS + Tailwind
```

---

## Security Workflow

**File:** `.github/workflows/security.yml`

**Triggers:**
- Weekly schedule (Monday 2 AM UTC)
- Manual dispatch

### Purpose

Comprehensive security audit that runs independently of CI to:
- Generate SARIF reports for GitHub Security tab
- Audit all dependencies for known vulnerabilities
- Provide detailed security artifacts

### Jobs

```yaml
security-audit:
  - Bandit SARIF report → GitHub Security tab
  - pip-audit JSON report → Artifacts
```

**Artifacts:**
- `security-reports` - Bandit SARIF + pip-audit JSON (30-day retention)

---

## Dependabot

**File:** `.github/dependabot.yml`

Automatically creates PRs for dependency updates.

| Ecosystem | Directory | Schedule | PR Limit |
|-----------|-----------|----------|----------|
| pip | / | Weekly (Monday) | 5 |
| npm | / | Weekly (Monday) | 3 |
| npm | /frontend | Weekly (Monday) | 5 |
| github-actions | / | Weekly | 3 |

**Grouping:** Minor and patch updates are grouped to reduce PR noise.

**Commit Prefixes:**
- `deps(py):` - Python dependencies
- `deps(css):` - Root NPM (Tailwind)
- `deps(frontend):` - React dependencies
- `deps(actions):` - GitHub Actions

---

## Troubleshooting

### CI is slow

1. Check cache hit rate in job logs
2. Ensure `package-lock.json` and `uv.lock` are committed
3. Review if any jobs can be parallelized further

### backend-lint fails

```bash
# Fix automatically
uv run ruff check . --fix
uv run ruff format .
```

### frontend-build fails with type errors

```bash
cd frontend
npx tsc --noEmit  # See all type errors
```

### docker-build fails

1. Check Dockerfile syntax
2. Verify base image availability
3. Check build context (`.dockerignore`)

### Security scan shows vulnerabilities

1. Check if vulnerability has a fix available
2. Update affected dependency: `uv add package@latest`
3. If no fix, evaluate risk and document exception



---

# FILE: docs\prd\ci-cd.md

# PRD: CI/CD Pipeline

## Overview

Automated CI/CD pipeline for OpenAlgo v2 providing continuous integration, security scanning, and quality gates for the Flask backend and React frontend. Designed for minimal maintenance overhead and fast developer feedback.

## Problem Statement

Without automated CI/CD:
- Code quality issues slip into production
- Security vulnerabilities go undetected
- Manual testing is inconsistent and time-consuming
- Dependency updates are neglected
- Contributors may submit broken or insecure code

## Solution

A comprehensive GitHub Actions-based pipeline that:
- Runs automatically on every PR and push to main
- Validates both backend (Python) and frontend (React) code
- Scans for security vulnerabilities
- Builds and validates Docker images
- Provides fast feedback (< 5 minutes)

## Target Users

| Segment | Needs |
|---------|-------|
| Core Maintainers | Automated quality gates, security alerts |
| Contributors | Fast PR feedback, clear error messages |
| Deployers | Validated builds, security assurance |

## Functional Requirements

### FR1: Code Quality

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Python linting with Ruff | P0 |
| FR1.2 | Python formatting validation | P0 |
| FR1.3 | TypeScript/React linting with Biome | P0 |
| FR1.4 | Frontend build validation | P0 |

### FR2: Testing

| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Backend pytest execution | P0 |
| FR2.2 | Frontend Vitest unit tests | P0 |
| FR2.3 | Frontend Playwright E2E tests | P1 |
| FR2.4 | Coverage report generation | P1 |

### FR3: Security

| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Bandit static analysis | P1 |
| FR3.2 | pip-audit dependency scanning | P1 |
| FR3.3 | Trivy Docker image scanning | P1 |
| FR3.4 | Secrets detection | P1 |

### FR4: Automation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | Dependabot for Python deps | P1 |
| FR4.2 | Dependabot for NPM deps | P1 |
| FR4.3 | Dependabot for GitHub Actions | P1 |
| FR4.4 | Weekly security scan schedule | P2 |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| CI Runtime | < 5 minutes (parallel jobs) |
| Cache Hit Rate | > 80% on repeat builds |
| False Positive Rate | < 5% on security scans |
| Maintenance Overhead | < 30 min/week |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Triggers: push to main, PR to main                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ backend-lint │  │ frontend-    │  │    security-scan     │  │
│  │    (Ruff)    │  │    lint      │  │ (Bandit, pip-audit)  │  │
│  └──────────────┘  │   (Biome)    │  └──────────────────────┘  │
│                    └──────────────┘                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ backend-test │  │ frontend-    │  │    docker-build      │  │
│  │   (pytest)   │  │    build     │  │   (Buildx + Trivy)   │  │
│  └──────────────┘  │   (Vite)     │  └──────────────────────┘  │
│                    └──────────────┘                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ root-css-    │  │ frontend-    │  │    frontend-e2e      │  │
│  │    build     │  │    test      │  │    (Playwright)      │  │
│  └──────────────┘  │  (Vitest)    │  └──────────────────────┘  │
│                    └──────────────┘                              │
│                                                                  │
│  All jobs run in PARALLEL (~3-4 minutes total)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install pre-commit hooks (one-time setup)
pip install pre-commit
pre-commit install

# Run all checks locally before committing
pre-commit run --all-files

# Run backend tests
uv run pytest test/ -v

# Run frontend tests
cd frontend && npm test

# Run frontend E2E tests
cd frontend && npm run e2e
```

## File Structure

```
.github/
  workflows/
    ci.yml              # Main CI workflow (9 parallel jobs)
    security.yml        # Weekly security scan
  dependabot.yml        # Automated dependency updates

.pre-commit-config.yaml # Local pre-commit hooks
.secrets.baseline       # Secrets detection baseline
pyproject.toml          # Ruff + pytest configuration
```

## Related Documentation

- [Workflows Reference](./ci-cd-workflows.md) - Detailed job documentation
- [Security Scanning](./ci-cd-security.md) - Security tools and configuration
- [Local Development](./ci-cd-local-development.md) - Pre-commit setup guide

## Success Metrics

| Metric | Target |
|--------|--------|
| PR CI Pass Rate | > 95% |
| Mean CI Duration | < 4 minutes |
| Security Vulnerabilities in Prod | 0 critical |
| Dependency Freshness | < 30 days behind |



---

# FILE: docs\prd\event-bus.md

# Event Bus PRD

## Problem

Order side-effects (logging, SocketIO notifications, Telegram alerts) were hardcoded across 10+ service files with 50+ dispatch points. This caused:

- **Inconsistent behavior**: 3 different ownership patterns for side-effects (sandbox fires, caller fires, nobody fires)
- **Silent bugs**: `closeposition` in analyze mode fired zero side-effects (dead `if False:` block); `modify`/`cancel` in analyze mode had no Telegram alerts
- **Duplicate alerts**: Basket/split orders fired N per-order alerts + 1 summary
- **Tight coupling**: Adding a new consumer required editing 4-5 service files
- **Security gap**: API key leaked into log database on validation failure paths
- **Code duplication**: Identical `emit_analyzer_error()` helper copied into 8 files

## Solution

In-process Event Bus — a lightweight pub/sub system using Python stdlib (`threading.Lock` + `ThreadPoolExecutor`).

### Core Concept

Services publish typed events. Subscribers handle side-effects independently.

```
Service: bus.publish(OrderPlacedEvent(...))
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    Log to DB    SocketIO    Telegram
   (subscriber) (subscriber) (subscriber)
```

## Requirements

### Functional

| Requirement | Status |
|-------------|--------|
| All 10 order services publish events via bus | Complete |
| Log subscriber handles both live and analyze mode | Complete |
| SocketIO subscriber emits correct event names per type | Complete |
| Telegram subscriber sends alerts for all order types | Complete |
| Batch operations fire ONE summary event, not N+1 | Complete |
| Analyze mode events set `mode="analyze"` | Complete |
| API keys stripped from event `request_data` before publish | Complete |
| Subscriber failures isolated (one crash doesn't affect others) | Complete |
| New subscribers can be added without modifying services | Complete |

### Non-Functional

| Requirement | Status |
|-------------|--------|
| Zero new dependencies (stdlib only) | Complete |
| Zero infrastructure (no Redis, no ZeroMQ) | Complete |
| Non-blocking publish (ThreadPoolExecutor) | Complete |
| Thread-safe subscribe/unsubscribe | Complete |
| < 1ms publish overhead | Complete |

## Scope

### In Scope

- All order execution services (place, smart, basket, split, options, multi-order, modify, cancel, cancel-all, close-position)
- Sandbox service side-effect removal
- REST API validation error logging migration
- Blueprint `close_position` logging gap fix
- Telegram alert templates for `optionsorder` and `optionsmultiorder`

### Out of Scope (Future)

- Strategy-level position tracking (Phase 2 — new subscriber)
- Strategy-level risk management (Phase 2 — new subscriber)
- Event persistence/replay (SQLite event log table)
- Query services (`orderstatus`, `openposition`, `margin`)

## Bugs Fixed

| Bug | Impact |
|-----|--------|
| `closeposition` analyze mode: dead `if False:` block, zero side-effects | Position closes silently in analyzer |
| `modify`/`cancel` analyze mode: missing Telegram alerts | No notification for sandbox operations |
| `options_order`/`options_multiorder`: `order_event` fired in analyze mode | Wrong SocketIO event in analyzer |
| Basket/split: N+1 `analyzer_update` events and log entries | 21 log entries for 20-order basket |
| `blueprints/orders.py` `close_position`: no API logging | Orders placed but not logged |
| API key in `request_data` on validation failure | Raw key persisted to log DB |
| `emit_event=False` didn't suppress Telegram | Per-sub-order Telegram still fired |

## Architecture

See [Design Doc: 53-event-bus](../design/53-event-bus/README.md) for full technical details.

## Files Changed

### New Files (11)

| File | Lines | Purpose |
|------|-------|---------|
| `utils/event_bus.py` | ~70 | EventBus class |
| `events/__init__.py` | ~40 | Event type exports |
| `events/base.py` | ~25 | Base event dataclass |
| `events/order_events.py` | ~70 | Order event types |
| `events/batch_events.py` | ~60 | Batch event types |
| `events/position_events.py` | ~30 | Position event types |
| `events/analyzer_events.py` | ~15 | Analyzer error event |
| `subscribers/__init__.py` | ~90 | Subscriber registration |
| `subscribers/log_subscriber.py` | ~40 | DB logging |
| `subscribers/socketio_subscriber.py` | ~200 | SocketIO events |
| `subscribers/telegram_subscriber.py` | ~70 | Telegram alerts |

### Modified Files (19)

- 10 service files: hardcoded side-effects replaced with `bus.publish()`
- 7 restx_api files: validation error logging migrated
- 1 blueprint: `orders.py` close_position logging gap fixed
- 1 startup: `app.py` subscriber registration added



---

# FILE: docs\prd\flow-execution.md

# Flow Execution Engine

This document describes the backend execution engine that runs Flow workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Workflow Execution                              │
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   Trigger       │    │  Execution      │    │  Result         │ │
│  │   Sources       │───▶│  Engine         │───▶│  Storage        │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│         │                       │                      │            │
│  ┌──────┴──────┐        ┌──────┴──────┐        ┌──────┴──────┐    │
│  │ APScheduler │        │ Node        │        │ Database    │    │
│  │ Webhook     │        │ Executor    │        │ (SQLite)    │    │
│  │ Manual      │        │             │        │             │    │
│  └─────────────┘        └──────┬──────┘        └─────────────┘    │
│                                │                                    │
│                        ┌───────┴───────┐                           │
│                        │               │                           │
│                 ┌──────▼──────┐ ┌─────▼──────┐                    │
│                 │ Workflow    │ │ OpenAlgo   │                    │
│                 │ Context     │ │ Client     │                    │
│                 └─────────────┘ └────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### File Structure

```
services/
├── flow_executor_service.py    # Main execution engine (~1700 lines)
├── flow_openalgo_client.py     # OpenAlgo API wrapper (~500 lines)
└── flow_scheduler.py           # APScheduler integration
```

### Core Classes

| Class | Purpose |
|-------|---------|
| `WorkflowContext` | Maintains execution state and variables |
| `NodeExecutor` | Executes individual node operations |
| `FlowOpenAlgoClient` | Wraps OpenAlgo internal APIs |

## WorkflowContext

Manages state during workflow execution.

```python
class WorkflowContext:
    def __init__(self, webhook_data: dict = None):
        self.variables: Dict[str, Any] = {}
        self.condition_results: Dict[str, bool] = {}
        self.webhook_data = webhook_data or {}

    def set_variable(self, name: str, value: Any):
        """Store a variable for later use"""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Retrieve a stored variable"""
        return self.variables.get(name, default)

    def set_condition_result(self, node_id: str, result: bool):
        """Store condition result for edge routing"""
        self.condition_results[node_id] = result

    def get_condition_result(self, node_id: str) -> bool:
        """Get condition result for edge routing"""
        return self.condition_results.get(node_id, False)

    def interpolate(self, text: str) -> str:
        """Replace {{variable}} placeholders with values"""
        if not isinstance(text, str):
            return text

        # Built-in variables
        now = datetime.now()
        built_ins = {
            'timestamp': now.isoformat(),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'hour': str(now.hour),
            'minute': str(now.minute),
            'second': str(now.second),
            'weekday': now.strftime('%A'),
        }

        # Replace built-ins
        for key, value in built_ins.items():
            text = text.replace(f'{{{{{key}}}}}', value)

        # Replace user variables
        for key, value in self.variables.items():
            if isinstance(value, dict):
                # Support nested access: {{var.key}}
                for nested_key, nested_value in self._flatten_dict(value, key):
                    text = text.replace(f'{{{{{nested_key}}}}}', str(nested_value))
            else:
                text = text.replace(f'{{{{{key}}}}}', str(value))

        # Replace webhook data
        for key, value in self.webhook_data.items():
            text = text.replace(f'{{{{webhook.{key}}}}}', str(value))

        return text

    def _flatten_dict(self, d: dict, prefix: str):
        """Flatten nested dict for interpolation"""
        items = [(prefix, d)]
        for key, value in d.items():
            new_key = f'{prefix}.{key}'
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key))
            else:
                items.append((new_key, value))
        return items
```

### Variable Interpolation Examples

```python
# Built-in variables
context.interpolate("Current time: {{time}}")
# "Current time: 09:15:00"

# User variables
context.set_variable("quote", {"ltp": 625.50, "volume": 1000000})
context.interpolate("LTP is {{quote.ltp}}")
# "LTP is 625.5"

# Webhook data
# webhook_data = {"symbol": "RELIANCE", "action": "BUY"}
context.interpolate("Trade {{webhook.symbol}} with {{webhook.action}}")
# "Trade RELIANCE with BUY"
```

## NodeExecutor

Executes individual node operations.

```python
class NodeExecutor:
    def __init__(self, client: FlowOpenAlgoClient, context: WorkflowContext, logs: list):
        self.client = client
        self.context = context
        self.logs = logs

    # ========== Helper Methods ==========

    def get_str(self, data: dict, key: str, default: str = "") -> str:
        """Get string value with interpolation"""
        value = str(data.get(key, default) or default)
        return self.context.interpolate(value)

    def get_int(self, data: dict, key: str, default: int = 0) -> int:
        """Get integer value"""
        try:
            return int(data.get(key, default) or default)
        except (ValueError, TypeError):
            return default

    def get_float(self, data: dict, key: str, default: float = 0.0) -> float:
        """Get float value"""
        try:
            return float(data.get(key, default) or default)
        except (ValueError, TypeError):
            return default

    def get_bool(self, data: dict, key: str, default: bool = False) -> bool:
        """Get boolean value"""
        return bool(data.get(key, default))

    def store_output(self, node_data: dict, result: Any):
        """Store result in output variable if specified"""
        output_var = node_data.get("outputVariable")
        if output_var:
            self.context.set_variable(output_var, result)

    def log(self, message: str, level: str = "info"):
        """Add log entry"""
        self.logs.append({
            "time": datetime.now().isoformat(),
            "message": message,
            "level": level
        })

    # ========== Order Execution ==========

    def execute_place_order(self, node_data: dict) -> dict:
        """Execute place order node"""
        symbol = self.get_str(node_data, "symbol")
        exchange = self.get_str(node_data, "exchange", "NSE")
        action = self.get_str(node_data, "action", "BUY")
        quantity = self.get_int(node_data, "quantity", 1)
        product = self.get_str(node_data, "product", "MIS")
        price_type = self.get_str(node_data, "priceType", "MARKET")
        price = self.get_float(node_data, "price", 0)
        trigger_price = self.get_float(node_data, "triggerPrice", 0)

        if not symbol:
            return {"status": "error", "message": "Symbol is required"}

        self.log(f"Placing order: {action} {quantity} {symbol}.{exchange}")

        result = self.client.place_order(
            symbol=symbol,
            exchange=exchange,
            action=action,
            quantity=quantity,
            product=product,
            price_type=price_type,
            price=price,
            trigger_price=trigger_price
        )

        self.store_output(node_data, result)
        self.log(f"Order result: {result.get('status')} - {result.get('orderid', result.get('message'))}")

        return result

    def execute_smart_order(self, node_data: dict) -> dict:
        """Execute smart order (position-aware)"""
        symbol = self.get_str(node_data, "symbol")
        exchange = self.get_str(node_data, "exchange", "NSE")
        action = self.get_str(node_data, "action", "BUY")
        quantity = self.get_int(node_data, "quantity", 1)
        position_size = self.get_int(node_data, "positionSize", 0)
        product = self.get_str(node_data, "product", "MIS")
        price_type = self.get_str(node_data, "priceType", "MARKET")

        self.log(f"Smart order: {action} {symbol} qty={quantity} pos_size={position_size}")

        result = self.client.smart_order(
            symbol=symbol,
            exchange=exchange,
            action=action,
            quantity=quantity,
            position_size=position_size,
            product=product,
            price_type=price_type
        )

        self.store_output(node_data, result)
        return result

    # ========== Condition Execution ==========

    def execute_price_condition(self, node_data: dict, node_id: str) -> dict:
        """Execute price condition node"""
        symbol = self.get_str(node_data, "symbol")
        exchange = self.get_str(node_data, "exchange", "NSE")
        field = self.get_str(node_data, "field", "ltp")
        operator = self.get_str(node_data, "operator", ">")
        value = self.get_float(node_data, "value", 0)

        # Fetch current quote
        quote = self.client.get_quote(symbol, exchange)
        quote_data = quote.get("data", {})
        actual = float(quote_data.get(field, 0))

        # Evaluate condition
        result = self._evaluate_condition(actual, operator, value)

        # Store for edge routing
        self.context.set_condition_result(node_id, result)

        self.log(f"Price condition: {symbol}.{field} ({actual}) {operator} {value} = {result}")
        return {"result": result, "actual": actual, "expected": value}

    def execute_position_check(self, node_data: dict, node_id: str) -> dict:
        """Execute position check node"""
        symbol = self.get_str(node_data, "symbol")
        exchange = self.get_str(node_data, "exchange", "NSE")
        check_type = self.get_str(node_data, "checkType", "exists")
        threshold = self.get_int(node_data, "quantity", 0)

        # Get position
        position = self.client.get_open_position(symbol, exchange)
        quantity = abs(int(position.get("quantity", 0)))

        # Evaluate check
        if check_type == "exists":
            result = quantity != 0
        elif check_type == "quantity_gt":
            result = quantity > threshold
        elif check_type == "quantity_lt":
            result = quantity < threshold
        else:
            result = False

        self.context.set_condition_result(node_id, result)
        self.log(f"Position check: {symbol} qty={quantity} {check_type} = {result}")

        return {"result": result, "quantity": quantity}

    def execute_time_window(self, node_data: dict, node_id: str) -> dict:
        """Execute time window condition"""
        start_time = self.get_str(node_data, "startTime", "09:15")
        end_time = self.get_str(node_data, "endTime", "15:30")
        days = node_data.get("days", ["mon", "tue", "wed", "thu", "fri"])

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%a").lower()

        in_time = start_time <= current_time <= end_time
        in_day = current_day in days

        result = in_time and in_day

        self.context.set_condition_result(node_id, result)
        self.log(f"Time window: {current_time} in [{start_time}-{end_time}], {current_day} in {days} = {result}")

        return {"result": result}

    def _evaluate_condition(self, actual: float, operator: str, expected: float) -> bool:
        """Evaluate comparison condition"""
        if operator == ">":
            return actual > expected
        elif operator == "<":
            return actual < expected
        elif operator == "==":
            return actual == expected
        elif operator == ">=":
            return actual >= expected
        elif operator == "<=":
            return actual <= expected
        elif operator == "!=":
            return actual != expected
        return False

    # ========== Data Fetching ==========

    def execute_get_quote(self, node_data: dict) -> dict:
        """Execute get quote node"""
        symbol = self.get_str(node_data, "symbol")
        exchange = self.get_str(node_data, "exchange", "NSE")

        result = self.client.get_quote(symbol, exchange)

        self.store_output(node_data, result.get("data", {}))
        self.log(f"Got quote: {symbol}.{exchange} LTP={result.get('data', {}).get('ltp')}")

        return result

    def execute_get_positions(self, node_data: dict) -> dict:
        """Execute get positions node"""
        result = self.client.get_positions()

        self.store_output(node_data, result.get("data", []))
        self.log(f"Got positions: {len(result.get('data', []))} positions")

        return result

    # ========== Utility Operations ==========

    def execute_variable(self, node_data: dict) -> dict:
        """Execute variable node (set/get/math)"""
        operation = self.get_str(node_data, "operation", "set")
        var_name = self.get_str(node_data, "variableName")
        value = node_data.get("value")
        source_var = self.get_str(node_data, "sourceVariable")

        if operation == "set":
            self.context.set_variable(var_name, value)
            self.log(f"Set {var_name} = {value}")

        elif operation == "get":
            result = self.context.get_variable(var_name)
            return {"value": result}

        elif operation in ["add", "subtract", "multiply", "divide"]:
            source_value = self.context.get_variable(source_var, 0)
            if operation == "add":
                result = float(source_value) + float(value)
            elif operation == "subtract":
                result = float(source_value) - float(value)
            elif operation == "multiply":
                result = float(source_value) * float(value)
            elif operation == "divide":
                result = float(source_value) / float(value) if float(value) != 0 else 0

            self.context.set_variable(var_name, result)
            self.log(f"Calculated {var_name} = {result}")

        elif operation == "parse_json":
            import json
            try:
                parsed = json.loads(str(value))
                self.context.set_variable(var_name, parsed)
                self.log(f"Parsed JSON into {var_name}")
            except json.JSONDecodeError as e:
                self.log(f"JSON parse error: {e}", "error")
                return {"status": "error", "message": str(e)}

        return {"status": "success"}

    def execute_delay(self, node_data: dict) -> dict:
        """Execute delay node"""
        import time
        seconds = self.get_float(node_data, "seconds", 1)

        self.log(f"Waiting {seconds} seconds...")
        time.sleep(seconds)
        self.log(f"Delay complete")

        return {"status": "success"}

    def execute_log(self, node_data: dict) -> dict:
        """Execute log node"""
        message = self.get_str(node_data, "message")
        level = self.get_str(node_data, "level", "info")

        self.log(message, level)
        return {"status": "success", "message": message}

    def execute_telegram_alert(self, node_data: dict) -> dict:
        """Execute telegram alert node"""
        message = self.get_str(node_data, "message")

        result = self.client.send_telegram_alert(message)
        self.log(f"Telegram alert: {message[:50]}...")

        return result
```

## Workflow Execution

Main execution function.

```python
def execute_workflow(
    workflow_id: int,
    webhook_data: dict = None,
    api_key: str = None
) -> dict:
    """Execute a complete workflow"""

    # 1. Load workflow from database
    workflow = get_workflow(workflow_id)
    if not workflow:
        return {"status": "error", "message": "Workflow not found"}

    nodes = workflow.nodes
    edges = workflow.edges
    api_key = api_key or workflow.api_key

    if not api_key:
        return {"status": "error", "message": "No API key available"}

    # 2. Create execution context
    context = WorkflowContext(webhook_data=webhook_data)
    logs = []

    # 3. Create executor with OpenAlgo client
    client = FlowOpenAlgoClient(api_key)
    executor = NodeExecutor(client, context, logs)

    # 4. Build edge maps for traversal
    edge_map = {}  # source_id -> [edges]
    incoming_edge_map = {}  # target_id -> [edges]

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source not in edge_map:
            edge_map[source] = []
        edge_map[source].append(edge)

        if target not in incoming_edge_map:
            incoming_edge_map[target] = []
        incoming_edge_map[target].append(edge)

    # 5. Find trigger nodes (entry points)
    trigger_types = ["start", "webhookTrigger", "priceAlert", "httpRequest"]
    trigger_nodes = [n for n in nodes if n.get("type") in trigger_types]

    # 6. Execute from each trigger
    try:
        for trigger in trigger_nodes:
            execute_node_chain(
                node_id=trigger["id"],
                nodes=nodes,
                edge_map=edge_map,
                incoming_edge_map=incoming_edge_map,
                executor=executor,
                context=context,
                logs=logs,
                executed_nodes=set()
            )

        return {
            "status": "success",
            "logs": logs,
            "variables": context.variables
        }

    except Exception as e:
        logs.append({
            "time": datetime.now().isoformat(),
            "message": f"Execution error: {str(e)}",
            "level": "error"
        })
        return {
            "status": "error",
            "message": str(e),
            "logs": logs
        }
```

## Node Chain Execution

Recursive execution with edge following.

```python
def execute_node_chain(
    node_id: str,
    nodes: list,
    edge_map: dict,
    incoming_edge_map: dict,
    executor: NodeExecutor,
    context: WorkflowContext,
    logs: list,
    executed_nodes: set
):
    """Execute a node and follow outgoing edges"""

    # Prevent re-execution
    if node_id in executed_nodes:
        return
    executed_nodes.add(node_id)

    # Find node
    node = next((n for n in nodes if n["id"] == node_id), None)
    if not node:
        return

    node_type = node.get("type")
    node_data = node.get("data", {})

    logs.append({
        "time": datetime.now().isoformat(),
        "message": f"Executing node: {node_type}",
        "level": "info"
    })

    # Execute based on type
    result = None

    # Trigger nodes
    if node_type == "start":
        result = {"status": "success", "message": "Workflow started"}
    elif node_type == "webhookTrigger":
        result = {"status": "success", "data": context.webhook_data}

    # Action nodes
    elif node_type == "placeOrder":
        result = executor.execute_place_order(node_data)
    elif node_type == "smartOrder":
        result = executor.execute_smart_order(node_data)
    elif node_type == "optionsOrder":
        result = executor.execute_options_order(node_data)
    elif node_type == "cancelAllOrders":
        result = executor.execute_cancel_all_orders(node_data)
    elif node_type == "closePositions":
        result = executor.execute_close_positions(node_data)

    # Condition nodes
    elif node_type == "priceCondition":
        result = executor.execute_price_condition(node_data, node_id)
    elif node_type == "positionCheck":
        result = executor.execute_position_check(node_data, node_id)
    elif node_type == "fundCheck":
        result = executor.execute_fund_check(node_data, node_id)
    elif node_type == "timeWindow":
        result = executor.execute_time_window(node_data, node_id)
    elif node_type in ["andGate", "orGate", "notGate"]:
        result = executor.execute_logic_gate(node_data, node_id, node_type, incoming_edge_map, context)

    # Data nodes
    elif node_type == "getQuote":
        result = executor.execute_get_quote(node_data)
    elif node_type == "getDepth":
        result = executor.execute_get_depth(node_data)
    elif node_type == "positionBook":
        result = executor.execute_get_positions(node_data)
    elif node_type == "funds":
        result = executor.execute_get_funds(node_data)
    elif node_type == "history":
        result = executor.execute_get_history(node_data)

    # Utility nodes
    elif node_type == "variable":
        result = executor.execute_variable(node_data)
    elif node_type == "delay":
        result = executor.execute_delay(node_data)
    elif node_type == "log":
        result = executor.execute_log(node_data)
    elif node_type == "telegramAlert":
        result = executor.execute_telegram_alert(node_data)

    # Follow outgoing edges
    outgoing_edges = edge_map.get(node_id, [])

    for edge in outgoing_edges:
        target_id = edge.get("target")
        source_handle = edge.get("sourceHandle")

        # For conditional nodes, check which path to follow
        if source_handle in ["true", "false"]:
            condition_result = context.get_condition_result(node_id)
            should_follow = (source_handle == "true" and condition_result) or \
                          (source_handle == "false" and not condition_result)

            if not should_follow:
                continue

        # Execute next node
        execute_node_chain(
            node_id=target_id,
            nodes=nodes,
            edge_map=edge_map,
            incoming_edge_map=incoming_edge_map,
            executor=executor,
            context=context,
            logs=logs,
            executed_nodes=executed_nodes
        )
```

## FlowOpenAlgoClient

Wraps internal OpenAlgo APIs.

```python
class FlowOpenAlgoClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def place_order(
        self,
        symbol: str,
        exchange: str,
        action: str,
        quantity: int,
        product: str = "MIS",
        price_type: str = "MARKET",
        price: float = 0,
        trigger_price: float = 0
    ) -> dict:
        """Place an order using internal API"""
        from services.place_order_service import place_order_service

        return place_order_service(
            api_key=self.api_key,
            symbol=symbol,
            exchange=exchange,
            action=action,
            quantity=quantity,
            product=product,
            price_type=price_type,
            price=price,
            trigger_price=trigger_price
        )

    def smart_order(
        self,
        symbol: str,
        exchange: str,
        action: str,
        quantity: int,
        position_size: int,
        product: str = "MIS",
        price_type: str = "MARKET"
    ) -> dict:
        """Place smart order (position-aware)"""
        from services.smart_order_service import smart_order_service

        return smart_order_service(
            api_key=self.api_key,
            symbol=symbol,
            exchange=exchange,
            action=action,
            quantity=quantity,
            position_size=position_size,
            product=product,
            price_type=price_type
        )

    def get_quote(self, symbol: str, exchange: str) -> dict:
        """Get current quote"""
        from services.quote_service import get_quotes_service

        return get_quotes_service(
            api_key=self.api_key,
            symbol=symbol,
            exchange=exchange
        )

    def get_positions(self) -> dict:
        """Get all positions"""
        from services.position_service import get_positions_service

        return get_positions_service(api_key=self.api_key)

    def get_open_position(self, symbol: str, exchange: str) -> dict:
        """Get position for specific symbol"""
        from services.position_service import get_open_position_service

        return get_open_position_service(
            api_key=self.api_key,
            symbol=symbol,
            exchange=exchange
        )

    def send_telegram_alert(self, message: str) -> dict:
        """Send telegram notification"""
        from services.telegram_service import send_telegram_message

        return send_telegram_message(message)
```

## Scheduling

APScheduler integration for scheduled workflows.

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# IST timezone for Indian markets
IST = pytz.timezone('Asia/Kolkata')

scheduler = BackgroundScheduler(daemon=True, timezone=IST)

def schedule_workflow(workflow_id: int, schedule_config: dict) -> str:
    """Schedule a workflow for automatic execution"""
    schedule_type = schedule_config.get("scheduleType", "daily")
    time_str = schedule_config.get("time", "09:15")
    days = schedule_config.get("days", ["mon", "tue", "wed", "thu", "fri"])

    hour, minute = map(int, time_str.split(":"))

    if schedule_type == "daily":
        # Run daily at specified time
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=",".join(days[:3]),  # APScheduler format
            timezone=IST
        )

    elif schedule_type == "interval":
        interval_minutes = schedule_config.get("intervalMinutes", 5)
        from apscheduler.triggers.interval import IntervalTrigger
        trigger = IntervalTrigger(minutes=interval_minutes)

    elif schedule_type == "once":
        from apscheduler.triggers.date import DateTrigger
        run_date = schedule_config.get("runDate")
        trigger = DateTrigger(run_date=run_date, timezone=IST)

    # Add job
    job_id = f"workflow_{workflow_id}"
    scheduler.add_job(
        func=execute_workflow,
        trigger=trigger,
        args=[workflow_id],
        id=job_id,
        replace_existing=True
    )

    return job_id

def unschedule_workflow(job_id: str):
    """Remove scheduled workflow"""
    scheduler.remove_job(job_id)
```

## Database Models

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from database import Base

class FlowWorkflow(Base):
    __tablename__ = 'flow_workflows'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    nodes = Column(JSON, default=[])
    edges = Column(JSON, default=[])
    is_active = Column(Boolean, default=False)
    schedule_job_id = Column(String(255))
    webhook_token = Column(String(255), unique=True)
    webhook_secret = Column(String(255))
    webhook_enabled = Column(Boolean, default=False)
    webhook_auth_type = Column(String(50), default='payload')
    api_key = Column(String(255))  # Stored when activated
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class FlowWorkflowExecution(Base):
    __tablename__ = 'flow_workflow_executions'

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey('flow_workflows.id'))
    status = Column(String(50))  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    logs = Column(JSON, default=[])
    error = Column(Text)
```

## Webhook Handler

```python
from flask import Blueprint, request, jsonify

flow_bp = Blueprint('flow', __name__)

@flow_bp.route('/flow/webhook/<token>', methods=['POST'])
def handle_webhook(token: str):
    """Handle incoming webhook for workflow execution"""

    # Find workflow by token
    workflow = FlowWorkflow.query.filter_by(
        webhook_token=token,
        webhook_enabled=True
    ).first()

    if not workflow:
        return jsonify({"status": "error", "message": "Invalid webhook token"}), 404

    # Verify secret
    payload = request.get_json() or {}

    if workflow.webhook_auth_type == 'payload':
        # Secret in payload
        provided_secret = payload.get('secret')
        if provided_secret != workflow.webhook_secret:
            return jsonify({"status": "error", "message": "Invalid secret"}), 401

    elif workflow.webhook_auth_type == 'url':
        # Secret in URL parameter
        provided_secret = request.args.get('secret')
        if provided_secret != workflow.webhook_secret:
            return jsonify({"status": "error", "message": "Invalid secret"}), 401

    # Execute workflow
    result = execute_workflow(
        workflow_id=workflow.id,
        webhook_data=payload,
        api_key=workflow.api_key
    )

    # Store execution record
    execution = FlowWorkflowExecution(
        workflow_id=workflow.id,
        status=result.get('status'),
        started_at=datetime.now(),
        completed_at=datetime.now(),
        logs=result.get('logs', []),
        error=result.get('message') if result.get('status') == 'error' else None
    )
    db.session.add(execution)
    db.session.commit()

    return jsonify(result)
```

## Error Handling

```python
class FlowExecutionError(Exception):
    """Custom exception for flow execution errors"""
    pass

def safe_execute_node(executor: NodeExecutor, node_type: str, node_data: dict, node_id: str = None) -> dict:
    """Execute node with error handling"""
    try:
        # Map node type to executor method
        method_name = f"execute_{node_type}"
        if hasattr(executor, method_name):
            method = getattr(executor, method_name)
            if node_id:
                return method(node_data, node_id)
            return method(node_data)
        else:
            return {"status": "error", "message": f"Unknown node type: {node_type}"}

    except Exception as e:
        executor.log(f"Error executing {node_type}: {str(e)}", "error")
        return {"status": "error", "message": str(e)}
```



---

# FILE: docs\prd\flow-node-creation.md

# Flow Node Creation Guide

This guide explains how to create new nodes for the Flow visual workflow builder.

## Overview

Adding a new node requires changes in both the frontend (React component) and backend (Python executor). Each node needs:

1. **TypeScript interface** - Data structure definition
2. **React component** - Visual representation
3. **Node registration** - Export and register in node types
4. **Constants** - Default values and metadata
5. **Config panel UI** - Configuration form
6. **Backend executor** - Execution logic

## Directory Structure

```
frontend/src/
├── types/
│   └── flow.ts                    # TypeScript interfaces
├── lib/flow/
│   └── constants.ts               # Node definitions & defaults
├── components/flow/
│   ├── nodes/
│   │   ├── index.ts               # Node type registry
│   │   ├── BaseNode.tsx           # Base component
│   │   └── YourNewNode.tsx        # Your new node
│   └── panels/
│       └── ConfigPanel.tsx        # Configuration UI

services/
└── flow_executor_service.py       # Backend execution
```

## Step 1: Define TypeScript Interface

**File:** `frontend/src/types/flow.ts`

```typescript
// Add your node data interface
export interface YourNewNodeData {
  label?: string
  symbol?: string
  exchange?: string
  threshold?: number
  action?: 'BUY' | 'SELL'
  outputVariable?: string  // For storing results
}

// Add to the appropriate union type
export type ActionNodeData =
  | PlaceOrderNodeData
  | SmartOrderNodeData
  | YourNewNodeData  // Add here
  // ...
```

### Common Field Patterns

```typescript
// For nodes that fetch data and store in variable
outputVariable?: string

// For trading nodes
symbol?: string
exchange?: string  // NSE, NFO, BSE, etc.
action?: 'BUY' | 'SELL'
quantity?: number
product?: 'MIS' | 'CNC' | 'NRML'
priceType?: 'MARKET' | 'LIMIT' | 'SL' | 'SL-M'

// For condition nodes
operator?: '>' | '<' | '==' | '>=' | '<=' | '!='
value?: number

// For time-based nodes
time?: string  // HH:MM format
days?: string[]  // ['mon', 'tue', ...]
```

## Step 2: Create React Component

**File:** `frontend/src/components/flow/nodes/YourNewNode.tsx`

### Using BaseNode (Recommended)

```typescript
import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { YourIcon } from 'lucide-react'
import { BaseNode, NodeDataRow, NodeBadge } from './BaseNode'
import type { YourNewNodeData } from '@/types/flow'

interface YourNewNodeProps extends NodeProps {
  data: YourNewNodeData
}

export const YourNewNode = memo(({ data, selected }: YourNewNodeProps) => {
  return (
    <BaseNode
      category="action"  // trigger | action | condition | data | utility
      icon={<YourIcon className="h-3 w-3" />}
      title="Your Node"
      subtitle={data.symbol || 'Configure symbol'}
      hasInput={true}
      hasOutput={true}
      hasConditionalOutputs={false}  // true for condition nodes
    >
      {/* Display configured values */}
      {data.symbol && (
        <NodeDataRow label="Symbol" value={data.symbol} />
      )}
      {data.exchange && (
        <NodeDataRow label="Exchange" value={data.exchange} />
      )}
      {data.action && (
        <NodeBadge variant={data.action === 'BUY' ? 'buy' : 'sell'}>
          {data.action}
        </NodeBadge>
      )}
    </BaseNode>
  )
})

YourNewNode.displayName = 'YourNewNode'
```

### Manual Implementation (Full Control)

```typescript
import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { YourIcon } from 'lucide-react'
import type { YourNewNodeData } from '@/types/flow'

interface YourNewNodeProps extends NodeProps {
  data: YourNewNodeData
}

export const YourNewNode = memo(({ data, selected }: YourNewNodeProps) => {
  return (
    <div className={`workflow-node ${selected ? 'selected' : ''}`}>
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-primary !w-2 !h-2"
      />

      {/* Node content */}
      <div className="p-2 min-w-[140px]">
        {/* Header */}
        <div className="mb-1.5 flex items-center gap-1.5">
          <div className="node-icon bg-blue-500/10 text-blue-500">
            <YourIcon className="h-3 w-3" />
          </div>
          <div>
            <div className="text-xs font-medium">Your Node</div>
            <div className="text-[9px] text-muted-foreground">
              {data.symbol || 'Configure'}
            </div>
          </div>
        </div>

        {/* Data display */}
        <div className="space-y-0.5 text-[10px]">
          {data.symbol && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Symbol</span>
              <span className="font-mono">{data.symbol}</span>
            </div>
          )}
        </div>
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-primary !w-2 !h-2"
      />
    </div>
  )
})

YourNewNode.displayName = 'YourNewNode'
```

### Conditional Node (True/False Outputs)

```typescript
export const YourConditionNode = memo(({ data, selected }: Props) => {
  return (
    <BaseNode
      category="condition"
      icon={<GitBranch className="h-3 w-3" />}
      title="Your Condition"
      hasInput={true}
      hasConditionalOutputs={true}  // Adds true/false handles
    >
      {/* Content */}
    </BaseNode>
  )
})
```

## Step 3: Register the Node

**File:** `frontend/src/components/flow/nodes/index.ts`

```typescript
// Import your node
import { YourNewNode } from './YourNewNode'

// Export it
export { YourNewNode }

// Add to nodeTypes registry
export const nodeTypes = {
  // ... existing nodes
  yourNewNode: YourNewNode,
} as const
```

## Step 4: Add Constants

**File:** `frontend/src/lib/flow/constants.ts`

### Node Definition (for palette)

```typescript
export const NODE_DEFINITIONS = {
  ACTIONS: [
    // ... existing
    {
      type: 'yourNewNode',
      label: 'Your Node',
      description: 'Brief description of what it does',
      category: 'action',
    },
  ],
  // Or add to appropriate category:
  // TRIGGERS, CONDITIONS, DATA, UTILITIES
}
```

### Default Data

```typescript
export const DEFAULT_NODE_DATA: Record<string, unknown> = {
  // ... existing
  yourNewNode: {
    label: '',
    symbol: '',
    exchange: 'NSE',
    threshold: 0,
    action: 'BUY',
    outputVariable: '',
  },
}
```

## Step 5: Add Config Panel UI

**File:** `frontend/src/components/flow/panels/ConfigPanel.tsx`

Add a section for your node type:

```typescript
{nodeType === 'yourNewNode' && (
  <>
    {/* Symbol input */}
    <div className="space-y-2">
      <Label className="text-xs">Symbol</Label>
      <Input
        className="h-8"
        placeholder="RELIANCE"
        value={(nodeData.symbol as string) || ''}
        onChange={(e) => handleDataChange('symbol', e.target.value)}
      />
    </div>

    {/* Exchange dropdown */}
    <div className="space-y-2">
      <Label className="text-xs">Exchange</Label>
      <Select
        value={(nodeData.exchange as string) || 'NSE'}
        onValueChange={(value) => handleDataChange('exchange', value)}
      >
        <SelectTrigger className="h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {EXCHANGES.map((ex) => (
            <SelectItem key={ex} value={ex}>{ex}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>

    {/* Action radio buttons */}
    <div className="space-y-2">
      <Label className="text-xs">Action</Label>
      <RadioGroup
        value={(nodeData.action as string) || 'BUY'}
        onValueChange={(value) => handleDataChange('action', value)}
        className="flex gap-4"
      >
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="BUY" id="buy" />
          <Label htmlFor="buy" className="text-xs">BUY</Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="SELL" id="sell" />
          <Label htmlFor="sell" className="text-xs">SELL</Label>
        </div>
      </RadioGroup>
    </div>

    {/* Number input */}
    <div className="space-y-2">
      <Label className="text-xs">Threshold</Label>
      <Input
        type="number"
        className="h-8"
        placeholder="100"
        value={(nodeData.threshold as number) || ''}
        onChange={(e) => handleDataChange('threshold', parseFloat(e.target.value) || 0)}
      />
    </div>

    {/* Output variable */}
    <div className="space-y-2">
      <Label className="text-xs">Store Result In</Label>
      <Input
        className="h-8"
        placeholder="result"
        value={(nodeData.outputVariable as string) || ''}
        onChange={(e) => handleDataChange('outputVariable', e.target.value)}
      />
      <p className="text-[10px] text-muted-foreground">
        Access with {'{{result}}'} in other nodes
      </p>
    </div>
  </>
)}
```

### Common UI Components

```typescript
// Text input
<Input
  className="h-8"
  placeholder="Example"
  value={(nodeData.field as string) || ''}
  onChange={(e) => handleDataChange('field', e.target.value)}
/>

// Number input
<Input
  type="number"
  step="0.01"
  className="h-8"
  value={(nodeData.field as number) || ''}
  onChange={(e) => handleDataChange('field', parseFloat(e.target.value))}
/>

// Select dropdown
<Select
  value={(nodeData.field as string) || 'default'}
  onValueChange={(value) => handleDataChange('field', value)}
>
  <SelectTrigger className="h-8">
    <SelectValue />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="opt1">Option 1</SelectItem>
    <SelectItem value="opt2">Option 2</SelectItem>
  </SelectContent>
</Select>

// Checkbox/Switch
<div className="flex items-center space-x-2">
  <Switch
    checked={(nodeData.enabled as boolean) || false}
    onCheckedChange={(checked) => handleDataChange('enabled', checked)}
  />
  <Label className="text-xs">Enable feature</Label>
</div>

// Multi-select (days of week)
<ToggleGroup
  type="multiple"
  value={(nodeData.days as string[]) || []}
  onValueChange={(value) => handleDataChange('days', value)}
  className="flex flex-wrap gap-1"
>
  {['mon', 'tue', 'wed', 'thu', 'fri'].map((day) => (
    <ToggleGroupItem
      key={day}
      value={day}
      className="h-6 px-2 text-xs"
    >
      {day.toUpperCase()}
    </ToggleGroupItem>
  ))}
</ToggleGroup>

// Textarea
<Textarea
  className="min-h-[60px] text-xs"
  placeholder="Enter message..."
  value={(nodeData.message as string) || ''}
  onChange={(e) => handleDataChange('message', e.target.value)}
/>
```

## Step 6: Add Backend Executor

**File:** `services/flow_executor_service.py`

### Add Execution Method

```python
class NodeExecutor:
    # ... existing methods

    def execute_your_new_node(self, node_data: dict) -> dict:
        """Execute your new node"""
        # Get node parameters with interpolation
        symbol = self.context.interpolate(self.get_str(node_data, "symbol"))
        exchange = self.get_str(node_data, "exchange", "NSE")
        threshold = self.get_float(node_data, "threshold", 0)
        action = self.get_str(node_data, "action", "BUY")

        # Validate required fields
        if not symbol:
            return {"status": "error", "message": "Symbol is required"}

        # Execute your logic
        try:
            # Example: fetch data
            quote = self.client.get_quote(symbol, exchange)
            ltp = quote.get("data", {}).get("ltp", 0)

            # Example: conditional logic
            if ltp > threshold:
                result = self.client.place_order(
                    symbol=symbol,
                    exchange=exchange,
                    action=action,
                    quantity=1,
                    price_type="MARKET",
                    product="MIS"
                )
            else:
                result = {"status": "skipped", "message": f"LTP {ltp} <= threshold {threshold}"}

            # Store result in output variable if specified
            self.store_output(node_data, result)

            return result

        except Exception as e:
            self.log(f"Error in your_new_node: {str(e)}", "error")
            return {"status": "error", "message": str(e)}
```

### Register in Node Chain Executor

```python
def execute_node_chain(node_id, nodes, edge_map, executor, context, ...):
    # ... existing code

    # Add your node type
    elif node_type == "yourNewNode":
        result = executor.execute_your_new_node(node_data)

    # ... rest of code
```

### Helper Methods

```python
class NodeExecutor:
    def get_str(self, data: dict, key: str, default: str = "") -> str:
        """Get string value from node data"""
        return str(data.get(key, default) or default)

    def get_int(self, data: dict, key: str, default: int = 0) -> int:
        """Get integer value from node data"""
        try:
            return int(data.get(key, default) or default)
        except (ValueError, TypeError):
            return default

    def get_float(self, data: dict, key: str, default: float = 0.0) -> float:
        """Get float value from node data"""
        try:
            return float(data.get(key, default) or default)
        except (ValueError, TypeError):
            return default

    def get_bool(self, data: dict, key: str, default: bool = False) -> bool:
        """Get boolean value from node data"""
        return bool(data.get(key, default))

    def store_output(self, node_data: dict, result: dict):
        """Store result in output variable"""
        output_var = node_data.get("outputVariable")
        if output_var:
            self.context.set_variable(output_var, result)

    def log(self, message: str, level: str = "info"):
        """Add log entry"""
        self.logs.append({
            "time": datetime.now().isoformat(),
            "message": message,
            "level": level
        })
```

### Condition Node Pattern

```python
def execute_your_condition_node(self, node_data: dict, node_id: str) -> dict:
    """Execute condition node - returns True/False for branching"""
    value = self.get_float(node_data, "value")
    operator = self.get_str(node_data, "operator", ">")
    threshold = self.get_float(node_data, "threshold")

    # Evaluate condition
    result = False
    if operator == ">":
        result = value > threshold
    elif operator == "<":
        result = value < threshold
    elif operator == "==":
        result = value == threshold
    # ... more operators

    # Store condition result for edge routing
    self.context.set_condition_result(node_id, result)

    self.log(f"Condition: {value} {operator} {threshold} = {result}")
    return {"result": result}
```

## Variable Interpolation

The `WorkflowContext` supports variable interpolation with `{{variableName}}` syntax:

### Built-in Variables

| Variable | Description |
|----------|-------------|
| `{{timestamp}}` | Current ISO timestamp |
| `{{date}}` | Current date (YYYY-MM-DD) |
| `{{time}}` | Current time (HH:MM:SS) |
| `{{hour}}` | Current hour |
| `{{minute}}` | Current minute |
| `{{weekday}}` | Day name (Monday, etc.) |

### User Variables

Set via Variable node or `outputVariable` field:

```python
# In your executor
self.context.set_variable("myResult", {"ltp": 100.50})

# Access in other nodes
symbol = self.context.interpolate("{{myResult.ltp}}")  # "100.5"
```

### Nested Access

```python
# If variable contains: {"data": {"ltp": 100, "volume": 5000}}
self.context.interpolate("{{quote.data.ltp}}")  # "100"
```

## Complete Example: ATR Stop-Loss Node

### 1. TypeScript Interface

```typescript
export interface AtrStopLossNodeData {
  label?: string
  symbol?: string
  exchange?: string
  period?: number
  multiplier?: number
  action?: 'BUY' | 'SELL'
  outputVariable?: string
}
```

### 2. React Component

```typescript
export const AtrStopLossNode = memo(({ data, selected }: Props) => {
  return (
    <BaseNode
      category="data"
      icon={<TrendingDown className="h-3 w-3" />}
      title="ATR Stop-Loss"
      subtitle={data.symbol || 'Configure'}
      hasInput={true}
      hasOutput={true}
    >
      {data.symbol && <NodeDataRow label="Symbol" value={data.symbol} />}
      {data.period && <NodeDataRow label="Period" value={data.period} />}
      {data.multiplier && <NodeDataRow label="Multiplier" value={`${data.multiplier}x`} />}
    </BaseNode>
  )
})
```

### 3. Backend Executor

```python
def execute_atr_stop_loss(self, node_data: dict) -> dict:
    symbol = self.context.interpolate(self.get_str(node_data, "symbol"))
    exchange = self.get_str(node_data, "exchange", "NSE")
    period = self.get_int(node_data, "period", 14)
    multiplier = self.get_float(node_data, "multiplier", 2.0)
    action = self.get_str(node_data, "action", "BUY")

    # Fetch historical data
    history = self.client.get_history(symbol, exchange, "D", days=period + 5)
    df = pd.DataFrame(history.get("data", []))

    # Calculate ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean().iloc[-1]

    # Calculate stop-loss
    ltp = df['close'].iloc[-1]
    if action == "BUY":
        stop_loss = ltp - (atr * multiplier)
    else:
        stop_loss = ltp + (atr * multiplier)

    result = {
        "symbol": symbol,
        "ltp": ltp,
        "atr": round(atr, 2),
        "stop_loss": round(stop_loss, 2),
        "action": action
    }

    self.store_output(node_data, result)
    self.log(f"ATR Stop-Loss: {symbol} ATR={atr:.2f} SL={stop_loss:.2f}")

    return result
```

## Testing Your Node

1. **Frontend**: Run `npm run dev` in `/frontend`
2. **Check palette**: Your node should appear in the appropriate category
3. **Drag to canvas**: Verify it renders correctly
4. **Configure**: Test the config panel inputs
5. **Execute**: Create a simple workflow and test execution
6. **Check logs**: Verify execution logs show expected output

## Best Practices

1. **Use BaseNode** for consistent styling
2. **Memoize components** with `memo()` for performance
3. **Validate inputs** in backend executor
4. **Log meaningful messages** for debugging
5. **Store results** in outputVariable for chaining
6. **Handle errors gracefully** with try/catch
7. **Support interpolation** for dynamic values
8. **Add helpful placeholders** in config panel



---

# FILE: docs\prd\flow-node-reference.md

# Flow Node Reference

Complete reference for all 50+ nodes available in the Flow visual workflow builder.

## Node Categories

| Category | Count | Purpose |
|----------|-------|---------|
| [Triggers](#trigger-nodes) | 4 | Start workflow execution |
| [Actions](#action-nodes) | 10 | Execute trading operations |
| [Conditions](#condition-nodes) | 8 | Control flow with branching |
| [Data](#data-nodes) | 16 | Fetch market & account data |
| [Streaming](#streaming-nodes) | 4 | Real-time data subscriptions |
| [Utility](#utility-nodes) | 7 | Helper operations |

---

## Trigger Nodes

Trigger nodes start workflow execution. Every workflow must have at least one trigger.

### Start

Schedule-based workflow execution.

| Field | Type | Description |
|-------|------|-------------|
| scheduleType | `once` \| `daily` \| `weekly` \| `interval` | Execution frequency |
| time | string | Time in HH:MM format (IST) |
| days | string[] | Days of week for weekly schedule |
| intervalMinutes | number | Minutes between executions |

**Example:**
```
Schedule: Daily at 09:15 IST
Days: Mon, Tue, Wed, Thu, Fri
```

### Webhook Trigger

External HTTP webhook trigger.

| Field | Type | Description |
|-------|------|-------------|
| (auto) | - | Webhook URL and secret auto-generated |

**Webhook URL:** `POST /flow/webhook/<token>`

**Payload Format:**
```json
{
  "secret": "your_webhook_secret",
  "symbol": "RELIANCE",
  "action": "BUY"
}
```

### Price Alert

Trigger when price crosses threshold.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | NSE, NFO, BSE, etc. |
| field | string | ltp, open, high, low, close |
| operator | string | >, <, ==, >=, <= |
| value | number | Threshold value |

### HTTP Request

Trigger from external API response.

| Field | Type | Description |
|-------|------|-------------|
| url | string | API endpoint URL |
| method | string | GET, POST |
| headers | object | Request headers |
| body | string | Request body (POST) |

---

## Action Nodes

Action nodes execute trading operations.

### Place Order

Place a regular order.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | NSE, NFO, BSE, MCX, CDS, BFO |
| action | string | BUY, SELL |
| quantity | number | Order quantity |
| product | string | MIS, CNC, NRML |
| priceType | string | MARKET, LIMIT, SL, SL-M |
| price | number | Limit price (if LIMIT/SL) |
| triggerPrice | number | Trigger price (if SL/SL-M) |
| outputVariable | string | Store order result |

**Output:**
```json
{
  "status": "success",
  "orderid": "123456789"
}
```

### Smart Order

Position-aware order placement.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| action | string | BUY, SELL |
| quantity | number | Order quantity |
| positionSize | number | Target position size |
| product | string | MIS, CNC, NRML |
| priceType | string | MARKET, LIMIT |

**Behavior:**
- If `positionSize=10` and current position is 5, places order for 5
- If `positionSize=0`, closes existing position
- Handles long/short position transitions

### Options Order

Single-leg options trade.

| Field | Type | Description |
|-------|------|-------------|
| underlying | string | NIFTY, BANKNIFTY, etc. |
| expiry | string | Expiry date |
| strike | number | Strike price |
| optionType | string | CE, PE |
| action | string | BUY, SELL |
| quantity | number | Lot quantity |
| product | string | MIS, NRML |

### Options Multi-Order

Multi-leg options strategies.

| Field | Type | Description |
|-------|------|-------------|
| strategy | string | STRADDLE, STRANGLE, SPREAD, IRON_CONDOR |
| underlying | string | NIFTY, BANKNIFTY |
| expiry | string | Expiry date |
| atmStrike | number | ATM strike price |
| quantity | number | Lot quantity |
| action | string | BUY, SELL |

**Strategies:**
- **STRADDLE**: Same strike CE + PE
- **STRANGLE**: OTM CE + OTM PE
- **SPREAD**: Two strikes, same type
- **IRON_CONDOR**: Four legs

### Basket Order

Multiple orders in single execution.

| Field | Type | Description |
|-------|------|-------------|
| orders | array | Array of order objects |

**Order Object:**
```json
{
  "symbol": "SBIN",
  "exchange": "NSE",
  "action": "BUY",
  "quantity": 100
}
```

### Split Order

Large order splitting.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| action | string | BUY, SELL |
| totalQuantity | number | Total quantity |
| splitSize | number | Quantity per order |
| delayMs | number | Delay between orders (ms) |

### Modify Order

Modify existing order.

| Field | Type | Description |
|-------|------|-------------|
| orderId | string | Order ID to modify |
| quantity | number | New quantity |
| price | number | New price |
| triggerPrice | number | New trigger price |

### Cancel Order

Cancel specific order.

| Field | Type | Description |
|-------|------|-------------|
| orderId | string | Order ID to cancel |

### Cancel All Orders

Cancel all open orders.

| Field | Type | Description |
|-------|------|-------------|
| (none) | - | Cancels all pending orders |

### Close Positions

Square off all open positions.

| Field | Type | Description |
|-------|------|-------------|
| product | string | MIS, NRML, or ALL |

---

## Condition Nodes

Condition nodes control workflow branching with true/false outputs.

### Price Condition

Check price against threshold.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| field | string | ltp, open, high, low, close, volume |
| operator | string | >, <, ==, >=, <=, != |
| value | number | Comparison value |

**Outputs:**
- **true**: Condition met
- **false**: Condition not met

### Position Check

Check if position exists.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| checkType | string | exists, quantity_gt, quantity_lt |
| quantity | number | Quantity threshold |

### Fund Check

Check available funds.

| Field | Type | Description |
|-------|------|-------------|
| field | string | available_cash, used_margin, total |
| operator | string | >, <, == |
| value | number | Comparison value |

### Time Window

Check if within time range.

| Field | Type | Description |
|-------|------|-------------|
| startTime | string | Start time (HH:MM) |
| endTime | string | End time (HH:MM) |
| days | string[] | Days of week |

**Example:**
```
Start: 09:15, End: 15:15
Days: Mon, Tue, Wed, Thu, Fri
```

### Time Condition

Check specific time.

| Field | Type | Description |
|-------|------|-------------|
| time | string | Target time (HH:MM) |
| operator | string | before, after, at |

### AND Gate

Logical AND of multiple inputs.

| Field | Type | Description |
|-------|------|-------------|
| (inputs) | - | Connect multiple condition outputs |

**Behavior:** Returns true only if ALL inputs are true.

### OR Gate

Logical OR of multiple inputs.

| Field | Type | Description |
|-------|------|-------------|
| (inputs) | - | Connect multiple condition outputs |

**Behavior:** Returns true if ANY input is true.

### NOT Gate

Logical NOT (inversion).

| Field | Type | Description |
|-------|------|-------------|
| (input) | - | Single condition input |

**Behavior:** Inverts true ↔ false.

---

## Data Nodes

Data nodes fetch market and account information.

### Get Quote

Fetch current quote for symbol.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store result |

**Output:**
```json
{
  "ltp": 625.50,
  "open": 620.00,
  "high": 628.00,
  "low": 618.50,
  "close": 622.00,
  "volume": 1500000
}
```

### Get Depth

Fetch market depth.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store result |

**Output:**
```json
{
  "buy": [
    {"price": 625.45, "quantity": 1000, "orders": 5}
  ],
  "sell": [
    {"price": 625.50, "quantity": 800, "orders": 3}
  ]
}
```

### History

Fetch historical OHLCV data.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| interval | string | 1m, 5m, 15m, 30m, 1h, D |
| startDate | string | Start date (YYYY-MM-DD) |
| endDate | string | End date (YYYY-MM-DD) |
| outputVariable | string | Store result |

### Symbol

Get symbol information.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store result |

**Output:**
```json
{
  "symbol": "RELIANCE",
  "token": "2885",
  "lotSize": 1,
  "tickSize": 0.05
}
```

### Option Symbol

Resolve option symbol from parameters.

| Field | Type | Description |
|-------|------|-------------|
| underlying | string | NIFTY, BANKNIFTY |
| expiry | string | Expiry date |
| strike | number | Strike price |
| optionType | string | CE, PE |
| outputVariable | string | Store resolved symbol |

### Expiry Dates

Get available expiry dates.

| Field | Type | Description |
|-------|------|-------------|
| underlying | string | NIFTY, BANKNIFTY |
| outputVariable | string | Store expiry list |

### Option Chain

Fetch option chain data.

| Field | Type | Description |
|-------|------|-------------|
| underlying | string | NIFTY, BANKNIFTY |
| expiry | string | Expiry date |
| outputVariable | string | Store option chain |

### Open Position

Get position for specific symbol.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store position |

### Order Book

Get all orders.

| Field | Type | Description |
|-------|------|-------------|
| outputVariable | string | Store orders |

### Trade Book

Get all executed trades.

| Field | Type | Description |
|-------|------|-------------|
| outputVariable | string | Store trades |

### Position Book

Get all open positions.

| Field | Type | Description |
|-------|------|-------------|
| outputVariable | string | Store positions |

### Holdings

Get delivery holdings.

| Field | Type | Description |
|-------|------|-------------|
| outputVariable | string | Store holdings |

### Funds

Get account funds.

| Field | Type | Description |
|-------|------|-------------|
| outputVariable | string | Store funds |

**Output:**
```json
{
  "availablecash": 100000,
  "collateral": 50000,
  "m2mrealized": 500,
  "m2munrealized": -200
}
```

### Intervals

Get supported intervals for broker.

| Field | Type | Description |
|-------|------|-------------|
| outputVariable | string | Store intervals |

### Holidays

Get market holidays.

| Field | Type | Description |
|-------|------|-------------|
| year | number | Year |
| outputVariable | string | Store holidays |

### Timings

Get market timings.

| Field | Type | Description |
|-------|------|-------------|
| exchange | string | Exchange |
| outputVariable | string | Store timings |

---

## Streaming Nodes

Streaming nodes subscribe to real-time WebSocket data.

### Subscribe LTP

Subscribe to real-time LTP updates.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store streaming data |

### Subscribe Quote

Subscribe to real-time quote updates.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store streaming data |

### Subscribe Depth

Subscribe to real-time depth updates.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |
| outputVariable | string | Store streaming data |

### Unsubscribe

Unsubscribe from streaming data.

| Field | Type | Description |
|-------|------|-------------|
| symbol | string | Trading symbol |
| exchange | string | Exchange |

---

## Utility Nodes

Utility nodes provide helper operations.

### Variable

Set, get, or calculate variables.

| Field | Type | Description |
|-------|------|-------------|
| operation | string | set, get, add, subtract, multiply, divide, parse_json |
| variableName | string | Variable name |
| value | any | Value for set/math operations |
| sourceVariable | string | Source for math operations |

**Operations:**
- **set**: `variableName = value`
- **get**: Read variable value
- **add**: `variableName = sourceVariable + value`
- **subtract**: `variableName = sourceVariable - value`
- **multiply**: `variableName = sourceVariable * value`
- **divide**: `variableName = sourceVariable / value`
- **parse_json**: Parse JSON string to object

### Delay

Wait for specified duration.

| Field | Type | Description |
|-------|------|-------------|
| seconds | number | Seconds to wait |

### Wait Until

Wait until specific time.

| Field | Type | Description |
|-------|------|-------------|
| time | string | Target time (HH:MM) |

### Log

Log message to execution logs.

| Field | Type | Description |
|-------|------|-------------|
| message | string | Log message |
| level | string | info, warn, error |

**Supports interpolation:** `"LTP is {{quote.ltp}}"`

### Telegram Alert

Send Telegram notification.

| Field | Type | Description |
|-------|------|-------------|
| message | string | Alert message |
| chatId | string | Telegram chat ID (optional) |

**Requires:** Telegram bot configured in OpenAlgo settings.

### Math Expression

Evaluate mathematical expression.

| Field | Type | Description |
|-------|------|-------------|
| expression | string | Math expression |
| outputVariable | string | Store result |

**Example:** `"{{quote.ltp}} * 1.02"` → 2% above LTP

### Group

Visual grouping of nodes (no execution).

| Field | Type | Description |
|-------|------|-------------|
| label | string | Group label |

---

## Variable Interpolation

All text fields support `{{variable}}` interpolation:

### Built-in Variables

| Variable | Description |
|----------|-------------|
| `{{timestamp}}` | ISO timestamp |
| `{{date}}` | Current date |
| `{{time}}` | Current time |
| `{{hour}}` | Current hour |
| `{{minute}}` | Current minute |
| `{{weekday}}` | Day name |

### Accessing Node Outputs

```
{{quote.ltp}}           → LTP from quote
{{position.quantity}}   → Position quantity
{{order.orderid}}       → Order ID from result
{{funds.availablecash}} → Available cash
```

### Webhook Data

```
{{webhook.symbol}}      → Symbol from webhook payload
{{webhook.action}}      → Action from webhook payload
{{webhook.quantity}}    → Quantity from webhook payload
```



---

# FILE: docs\prd\flow-ui-components.md

# Flow UI Components Guide

This guide documents the React components that make up the Flow visual workflow builder.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FlowEditor Page                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    ReactFlow Canvas                              ││
│  │  ┌─────────────────────────────────────────────────────────────┐││
│  │  │                     Nodes                                    │││
│  │  │  StartNode, PlaceOrderNode, PriceConditionNode, etc.        │││
│  │  └─────────────────────────────────────────────────────────────┘││
│  │  ┌─────────────────────────────────────────────────────────────┐││
│  │  │                     Edges                                    │││
│  │  │  InsertableEdge (custom edge with node insertion)           │││
│  │  └─────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────┘│
│        │                    │                    │                   │
│  ┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐             │
│  │NodePalette│      │ ConfigPanel │      │  LogPanel │             │
│  │(Left)     │      │  (Right)    │      │ (Bottom)  │             │
│  └───────────┘      └─────────────┘      └───────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `pages/flow/FlowEditor.tsx` | Main editor page | ~300 |
| `components/flow/nodes/index.ts` | Node registry | ~220 |
| `components/flow/nodes/BaseNode.tsx` | Base node component | ~220 |
| `components/flow/panels/NodePalette.tsx` | Left sidebar | ~200 |
| `components/flow/panels/ConfigPanel.tsx` | Right sidebar | ~550 |
| `components/flow/panels/ExecutionLogPanel.tsx` | Bottom panel | ~100 |
| `components/flow/edges/InsertableEdge.tsx` | Custom edge | ~150 |
| `stores/flowWorkflowStore.ts` | Zustand state | ~150 |
| `lib/flow/constants.ts` | Node definitions | ~650 |
| `types/flow.ts` | TypeScript types | ~750 |

## Main Editor

**File:** `frontend/src/pages/flow/FlowEditor.tsx`

```typescript
import { ReactFlow, Background, Controls, MiniMap, Panel } from '@xyflow/react'
import { nodeTypes } from '@/components/flow/nodes'
import { edgeTypes } from '@/components/flow/edges'
import { NodePalette } from '@/components/flow/panels/NodePalette'
import { ConfigPanel } from '@/components/flow/panels/ConfigPanel'
import { useFlowWorkflowStore } from '@/stores/flowWorkflowStore'

export function FlowEditor() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    selectedNodeId,
  } = useFlowWorkflowStore()

  return (
    <div className="h-screen w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
      >
        <Background variant="dots" gap={15} />
        <Controls />
        <MiniMap />

        {/* Left Panel - Node Palette */}
        <Panel position="top-left">
          <NodePalette />
        </Panel>

        {/* Right Panel - Config */}
        <Panel position="top-right">
          {selectedNodeId && <ConfigPanel />}
        </Panel>
      </ReactFlow>

      {/* Bottom Panel - Logs */}
      <ExecutionLogPanel />
    </div>
  )
}
```

## Node Components

### Base Node

**File:** `frontend/src/components/flow/nodes/BaseNode.tsx`

Provides consistent styling and handles for all nodes.

```typescript
interface BaseNodeProps {
  category: 'trigger' | 'action' | 'condition' | 'data' | 'utility'
  icon: ReactNode
  title: string
  subtitle?: string
  hasInput?: boolean
  hasOutput?: boolean
  hasConditionalOutputs?: boolean
  children?: ReactNode
}

export function BaseNode({
  category,
  icon,
  title,
  subtitle,
  hasInput = true,
  hasOutput = true,
  hasConditionalOutputs = false,
  children,
}: BaseNodeProps) {
  // Category-based colors
  const categoryColors = {
    trigger: 'bg-green-500/10 text-green-500 border-green-500/20',
    action: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    condition: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    data: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
    utility: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  }

  return (
    <div className={`workflow-node ${categoryColors[category]}`}>
      {/* Input Handle */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Top}
          className="!bg-primary !w-2 !h-2"
        />
      )}

      {/* Node Content */}
      <div className="p-2 min-w-[140px]">
        <div className="mb-1.5 flex items-center gap-1.5">
          <div className="node-icon">{icon}</div>
          <div>
            <div className="text-xs font-medium">{title}</div>
            {subtitle && (
              <div className="text-[9px] text-muted-foreground">{subtitle}</div>
            )}
          </div>
        </div>
        {children}
      </div>

      {/* Output Handle(s) */}
      {hasOutput && !hasConditionalOutputs && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!bg-primary !w-2 !h-2"
        />
      )}

      {/* Conditional Outputs (True/False) */}
      {hasConditionalOutputs && (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            className="!bg-green-500 !w-2 !h-2"
            style={{ left: '30%' }}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            className="!bg-red-500 !w-2 !h-2"
            style={{ left: '70%' }}
          />
        </>
      )}
    </div>
  )
}
```

### Helper Components

```typescript
// Display key-value data row
export function NodeDataRow({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string | number
  mono?: boolean
}) {
  return (
    <div className="flex justify-between text-[10px]">
      <span className="text-muted-foreground">{label}</span>
      <span className={mono ? 'font-mono' : ''}>{value}</span>
    </div>
  )
}

// Badge for buy/sell actions
export function NodeBadge({
  variant = 'default',
  children,
}: {
  variant?: 'buy' | 'sell' | 'default'
  children: ReactNode
}) {
  const colors = {
    buy: 'bg-green-500/10 text-green-500',
    sell: 'bg-red-500/10 text-red-500',
    default: 'bg-gray-500/10 text-gray-500',
  }

  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] ${colors[variant]}`}>
      {children}
    </span>
  )
}

// Info row with multiple items
export function NodeInfoRow({ items }: { items: Array<{ label: string; value: string }> }) {
  return (
    <div className="flex gap-2 text-[9px]">
      {items.map((item, i) => (
        <span key={i} className="text-muted-foreground">
          {item.label}: <span className="text-foreground">{item.value}</span>
        </span>
      ))}
    </div>
  )
}
```

### Node Type Registry

**File:** `frontend/src/components/flow/nodes/index.ts`

```typescript
import { StartNode } from './StartNode'
import { PlaceOrderNode } from './PlaceOrderNode'
import { SmartOrderNode } from './SmartOrderNode'
import { PriceConditionNode } from './PriceConditionNode'
// ... 50+ imports

export {
  StartNode,
  PlaceOrderNode,
  SmartOrderNode,
  PriceConditionNode,
  // ... exports
}

// Registry for ReactFlow
export const nodeTypes = {
  start: StartNode,
  placeOrder: PlaceOrderNode,
  smartOrder: SmartOrderNode,
  priceCondition: PriceConditionNode,
  optionsOrder: OptionsOrderNode,
  optionsMultiOrder: OptionsMultiOrderNode,
  basketOrder: BasketOrderNode,
  splitOrder: SplitOrderNode,
  modifyOrder: ModifyOrderNode,
  cancelOrder: CancelOrderNode,
  cancelAllOrders: CancelAllOrdersNode,
  closePositions: ClosePositionsNode,
  positionCheck: PositionCheckNode,
  fundCheck: FundCheckNode,
  timeWindow: TimeWindowNode,
  timeCondition: TimeConditionNode,
  andGate: AndGateNode,
  orGate: OrGateNode,
  notGate: NotGateNode,
  getQuote: GetQuoteNode,
  getDepth: GetDepthNode,
  history: HistoryNode,
  openPosition: OpenPositionNode,
  orderBook: OrderBookNode,
  tradeBook: TradeBookNode,
  positionBook: PositionBookNode,
  holdings: HoldingsNode,
  funds: FundsNode,
  symbol: SymbolNode,
  optionSymbol: OptionSymbolNode,
  expiry: ExpiryNode,
  optionChain: OptionChainNode,
  intervals: IntervalsNode,
  holidays: HolidaysNode,
  timings: TimingsNode,
  subscribeLtp: SubscribeLTPNode,
  subscribeQuote: SubscribeQuoteNode,
  subscribeDepth: SubscribeDepthNode,
  unsubscribe: UnsubscribeNode,
  variable: VariableNode,
  delay: DelayNode,
  waitUntil: WaitUntilNode,
  log: LogNode,
  telegramAlert: TelegramAlertNode,
  mathExpression: MathExpressionNode,
  webhookTrigger: WebhookTriggerNode,
  priceAlert: PriceAlertNode,
  httpRequest: HttpRequestNode,
  group: GroupNode,
} as const
```

## Panels

### Node Palette

**File:** `frontend/src/components/flow/panels/NodePalette.tsx`

Drag-and-drop node selection panel.

```typescript
import { NODE_DEFINITIONS } from '@/lib/flow/constants'

export function NodePalette() {
  const onDragStart = (event: DragEvent, nodeType: string) => {
    event.dataTransfer?.setData('application/reactflow', nodeType)
    event.dataTransfer!.effectAllowed = 'move'
  }

  return (
    <div className="w-64 bg-background border rounded-lg shadow-lg">
      <Tabs defaultValue="triggers">
        <TabsList className="w-full">
          <TabsTrigger value="triggers">Triggers</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
          <TabsTrigger value="conditions">Conditions</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
          <TabsTrigger value="utility">Utility</TabsTrigger>
        </TabsList>

        <TabsContent value="triggers">
          {NODE_DEFINITIONS.TRIGGERS.map((node) => (
            <div
              key={node.type}
              className="p-2 border-b cursor-grab hover:bg-accent"
              draggable
              onDragStart={(e) => onDragStart(e, node.type)}
            >
              <div className="font-medium text-sm">{node.label}</div>
              <div className="text-xs text-muted-foreground">
                {node.description}
              </div>
            </div>
          ))}
        </TabsContent>

        {/* Similar for other categories */}
      </Tabs>
    </div>
  )
}
```

### Config Panel

**File:** `frontend/src/components/flow/panels/ConfigPanel.tsx`

Dynamic configuration form based on selected node type.

```typescript
import { useFlowWorkflowStore } from '@/stores/flowWorkflowStore'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Label } from '@/components/ui/label'

export function ConfigPanel() {
  const { nodes, selectedNodeId, updateNodeData } = useFlowWorkflowStore()

  const selectedNode = nodes.find((n) => n.id === selectedNodeId)
  if (!selectedNode) return null

  const nodeType = selectedNode.type
  const nodeData = selectedNode.data

  const handleDataChange = (key: string, value: any) => {
    updateNodeData(selectedNodeId!, { [key]: value })
  }

  return (
    <div className="w-80 bg-background border rounded-lg shadow-lg p-4">
      <h3 className="font-semibold mb-4">Configure Node</h3>

      {/* Dynamic form based on node type */}
      {nodeType === 'placeOrder' && (
        <>
          <div className="space-y-2">
            <Label className="text-xs">Symbol</Label>
            <Input
              className="h-8"
              placeholder="RELIANCE"
              value={(nodeData.symbol as string) || ''}
              onChange={(e) => handleDataChange('symbol', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Exchange</Label>
            <Select
              value={(nodeData.exchange as string) || 'NSE'}
              onValueChange={(v) => handleDataChange('exchange', v)}
            >
              <SelectTrigger className="h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXCHANGES.map((ex) => (
                  <SelectItem key={ex} value={ex}>{ex}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Action</Label>
            <RadioGroup
              value={(nodeData.action as string) || 'BUY'}
              onValueChange={(v) => handleDataChange('action', v)}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="BUY" id="buy" />
                <Label htmlFor="buy">BUY</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="SELL" id="sell" />
                <Label htmlFor="sell">SELL</Label>
              </div>
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Quantity</Label>
            <Input
              type="number"
              className="h-8"
              placeholder="1"
              value={(nodeData.quantity as number) || ''}
              onChange={(e) => handleDataChange('quantity', parseInt(e.target.value))}
            />
          </div>
        </>
      )}

      {nodeType === 'priceCondition' && (
        <>
          {/* Price condition fields */}
        </>
      )}

      {/* ... 50+ node type configurations */}
    </div>
  )
}
```

### Execution Log Panel

**File:** `frontend/src/components/flow/panels/ExecutionLogPanel.tsx`

```typescript
interface LogEntry {
  time: string
  message: string
  level: 'info' | 'warn' | 'error'
}

export function ExecutionLogPanel({ logs }: { logs: LogEntry[] }) {
  return (
    <div className="h-48 bg-background border-t overflow-auto">
      <div className="p-2">
        <h4 className="text-sm font-semibold mb-2">Execution Logs</h4>
        <div className="space-y-1 font-mono text-xs">
          {logs.map((log, i) => (
            <div
              key={i}
              className={cn(
                'flex gap-2',
                log.level === 'error' && 'text-red-500',
                log.level === 'warn' && 'text-amber-500'
              )}
            >
              <span className="text-muted-foreground">[{log.time}]</span>
              <span>{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

## Custom Edge

**File:** `frontend/src/components/flow/edges/InsertableEdge.tsx`

Custom edge that allows inserting nodes mid-connection.

```typescript
import { BaseEdge, EdgeProps, getBezierPath } from '@xyflow/react'

export function InsertableEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  sourceHandleId,
  style = {},
  markerEnd,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  // Color based on condition handle
  const edgeColor = sourceHandleId === 'true'
    ? '#22c55e'  // green
    : sourceHandleId === 'false'
    ? '#ef4444'  // red
    : '#6b7280'  // gray

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{ ...style, stroke: edgeColor }}
      />

      {/* Insert button */}
      <foreignObject
        width={20}
        height={20}
        x={labelX - 10}
        y={labelY - 10}
        className="edge-insert-button"
      >
        <button
          className="w-5 h-5 rounded-full bg-primary text-white flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
          onClick={() => {/* Insert node logic */}}
        >
          +
        </button>
      </foreignObject>

      {/* Condition label */}
      {sourceHandleId && (
        <text
          x={labelX}
          y={labelY - 15}
          className="text-[10px] fill-muted-foreground"
          textAnchor="middle"
        >
          {sourceHandleId}
        </text>
      )}
    </>
  )
}

export const edgeTypes = {
  insertable: InsertableEdge,
}
```

## State Management

**File:** `frontend/src/stores/flowWorkflowStore.ts`

Zustand store for workflow state.

```typescript
import { create } from 'zustand'
import { Node, Edge, Connection, applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react'

interface WorkflowState {
  // Workflow data
  id: number | null
  name: string
  nodes: Node[]
  edges: Edge[]
  isActive: boolean

  // Selection
  selectedNodeId: string | null

  // Actions
  setWorkflow: (workflow: any) => void
  setNodes: (nodes: Node[]) => void
  setEdges: (edges: Edge[]) => void
  updateNodeData: (nodeId: string, data: Partial<any>) => void
  onNodesChange: (changes: any[]) => void
  onEdgesChange: (changes: any[]) => void
  onConnect: (connection: Connection) => void
  setSelectedNodeId: (nodeId: string | null) => void
  deleteSelected: () => void
  addNode: (type: string, position: { x: number; y: number }) => void
}

export const useFlowWorkflowStore = create<WorkflowState>((set, get) => ({
  id: null,
  name: '',
  nodes: [],
  edges: [],
  isActive: false,
  selectedNodeId: null,

  setWorkflow: (workflow) => set({
    id: workflow.id,
    name: workflow.name,
    nodes: workflow.nodes || [],
    edges: workflow.edges || [],
    isActive: workflow.is_active,
  }),

  setNodes: (nodes) => set({ nodes }),

  setEdges: (edges) => set({ edges }),

  updateNodeData: (nodeId, data) => set((state) => ({
    nodes: state.nodes.map((node) =>
      node.id === nodeId
        ? { ...node, data: { ...node.data, ...data } }
        : node
    ),
  })),

  onNodesChange: (changes) => set((state) => ({
    nodes: applyNodeChanges(changes, state.nodes),
  })),

  onEdgesChange: (changes) => set((state) => ({
    edges: applyEdgeChanges(changes, state.edges),
  })),

  onConnect: (connection) => set((state) => ({
    edges: addEdge(
      { ...connection, type: 'insertable' },
      state.edges
    ),
  })),

  setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),

  deleteSelected: () => set((state) => {
    if (!state.selectedNodeId) return state
    return {
      nodes: state.nodes.filter((n) => n.id !== state.selectedNodeId),
      edges: state.edges.filter(
        (e) => e.source !== state.selectedNodeId && e.target !== state.selectedNodeId
      ),
      selectedNodeId: null,
    }
  }),

  addNode: (type, position) => set((state) => {
    const newNode: Node = {
      id: `${type}_${Date.now()}`,
      type,
      position,
      data: DEFAULT_NODE_DATA[type] || {},
    }
    return { nodes: [...state.nodes, newNode] }
  }),
}))
```

## Constants

**File:** `frontend/src/lib/flow/constants.ts`

```typescript
// Node definitions for palette
export const NODE_DEFINITIONS = {
  TRIGGERS: [
    { type: 'start', label: 'Start', description: 'Schedule-based trigger', category: 'trigger' },
    { type: 'webhookTrigger', label: 'Webhook', description: 'External HTTP trigger', category: 'trigger' },
    { type: 'priceAlert', label: 'Price Alert', description: 'Price condition trigger', category: 'trigger' },
    { type: 'httpRequest', label: 'HTTP Request', description: 'API request trigger', category: 'trigger' },
  ],
  ACTIONS: [
    { type: 'placeOrder', label: 'Place Order', description: 'Place regular order', category: 'action' },
    { type: 'smartOrder', label: 'Smart Order', description: 'Position-aware order', category: 'action' },
    // ... more nodes
  ],
  CONDITIONS: [...],
  DATA: [...],
  UTILITIES: [...],
}

// Default node data
export const DEFAULT_NODE_DATA: Record<string, any> = {
  start: {
    scheduleType: 'daily',
    time: '09:15',
    days: ['mon', 'tue', 'wed', 'thu', 'fri'],
  },
  placeOrder: {
    symbol: '',
    exchange: 'NSE',
    action: 'BUY',
    quantity: 1,
    product: 'MIS',
    priceType: 'MARKET',
  },
  // ... more defaults
}

// Dropdown options
export const EXCHANGES = ['NSE', 'NFO', 'BSE', 'MCX', 'CDS', 'BFO']
export const PRODUCTS = ['MIS', 'CNC', 'NRML']
export const PRICE_TYPES = ['MARKET', 'LIMIT', 'SL', 'SL-M']
export const OPTIONS_STRATEGIES = ['STRADDLE', 'STRANGLE', 'SPREAD', 'IRON_CONDOR']
export const OPERATORS = ['>', '<', '==', '>=', '<=', '!=']
export const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
```

## UI Component Library

Flow uses **shadcn/ui** components:

| Component | Usage |
|-----------|-------|
| `Input` | Text/number inputs |
| `Select` | Dropdown selections |
| `RadioGroup` | Radio button groups |
| `Switch` | Toggle switches |
| `Tabs` | Tab navigation |
| `Label` | Form labels |
| `Button` | Action buttons |
| `Textarea` | Multi-line text |
| `ToggleGroup` | Multi-select (days) |

## Styling

### Node Styles

```css
/* workflow-node base styles */
.workflow-node {
  @apply bg-background border rounded-lg shadow-sm;
  @apply transition-all duration-200;
}

.workflow-node.selected {
  @apply ring-2 ring-primary;
}

.workflow-node:hover {
  @apply shadow-md;
}

/* Category colors */
.node-trigger { @apply border-green-500/30; }
.node-action { @apply border-blue-500/30; }
.node-condition { @apply border-amber-500/30; }
.node-data { @apply border-purple-500/30; }
.node-utility { @apply border-gray-500/30; }
```

### Icon Styles

```css
.node-icon {
  @apply w-6 h-6 rounded flex items-center justify-center;
}
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `@xyflow/react` | Visual workflow canvas |
| `zustand` | State management |
| `lucide-react` | Icons |
| `@radix-ui/*` | UI primitives |
| `tailwindcss` | Styling |



---

# FILE: docs\prd\flow.md

# PRD: Flow - Visual Workflow Automation

> **Status:** ✅ Stable - Fully implemented with 53 node types

## Overview

Flow is a no-code visual workflow builder that enables traders to create automated trading strategies using drag-and-drop nodes. Built with React Flow for the visual canvas and a Python-based execution engine.

## Problem Statement

Many traders have trading ideas but:
- Cannot write code (Python/Pine Script)
- Find webhook setup complex
- Need conditional logic (if price > X, then buy)
- Want to combine multiple signals

## Solution

A visual canvas where users:
- Drag nodes (triggers, conditions, actions)
- Connect them with edges
- Configure parameters via forms
- Activate to run automatically

## Target Users

| User | Use Case |
|------|----------|
| Non-coder Trader | Automate simple strategies |
| Signal Follower | Route TradingView alerts with conditions |
| Multi-strategy Trader | Manage multiple workflows visually |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    @xyflow/react Canvas                          ││
│  │  [Start] ──▶ [Price Check] ──▶ [Place Order] ──▶ [Telegram]     ││
│  └─────────────────────────────────────────────────────────────────┘│
│        │                    │                    │                   │
│  ┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐             │
│  │Node Palette│      │Config Panel │      │ Log Panel │             │
│  └───────────┘      └─────────────┘      └───────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Flask Backend                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                   Execution Engine                               ││
│  │  WorkflowContext │ NodeExecutor │ FlowOpenAlgoClient            ││
│  └─────────────────────────────────────────────────────────────────┘│
│        │                    │                    │                   │
│  ┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐             │
│  │APScheduler│      │Price Monitor│      │  Webhook  │             │
│  │  (IST)    │      │             │      │  Handler  │             │
│  └───────────┘      └─────────────┘      └───────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Node Categories (53 nodes verified)

| Category | Count | Examples |
|----------|-------|----------|
| Triggers | 5 | Start, Webhook, PriceAlert, HttpRequest, WaitUntil |
| Actions | 12 | PlaceOrder, SmartOrder, OptionsOrder, BasketOrder, SplitOrder, ModifyOrder, CancelOrder |
| Conditions | 9 | PriceCondition, TimeWindow, TimeCondition, PositionCheck, FundCheck, AndGate, OrGate, NotGate |
| Data | 17 | GetQuote, MultiQuotes, GetDepth, PositionBook, OrderBook, TradeBook, Holdings, Funds, Margin, OptionChain, OptionSymbol, History |
| Streaming | 4 | SubscribeLTP, SubscribeQuote, SubscribeDepth, Unsubscribe |
| Utility | 6 | Variable, Delay, Log, TelegramAlert, MathExpression, Symbol |

## Functional Requirements

### FR1: Workflow Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Create/edit/delete workflows | P0 |
| FR1.2 | Activate/deactivate workflows | P0 |
| FR1.3 | Duplicate workflow | P2 |
| FR1.4 | Import/export as JSON | P1 |

### FR2: Trigger Nodes
| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Scheduled trigger (daily, weekly, interval) | P0 |
| FR2.2 | Webhook trigger (external HTTP) | P0 |
| FR2.3 | Price alert trigger (LTP crosses X) | P1 |
| FR2.4 | Manual trigger (button click) | P0 |

### FR3: Condition Nodes
| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Price condition (>, <, ==) | P0 |
| FR3.2 | Time window (9:15-15:30) | P0 |
| FR3.3 | Position check (has open position?) | P1 |
| FR3.4 | Fund check (available margin > X) | P1 |
| FR3.5 | Logic gates (AND, OR, NOT) | P1 |

### FR4: Action Nodes
| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | Place order | P0 |
| FR4.2 | Smart order (position-aware) | P0 |
| FR4.3 | Options order (single leg) | P1 |
| FR4.4 | Options multi-order (strategies) | P1 |
| FR4.5 | Basket order | P2 |
| FR4.6 | Cancel/modify orders | P1 |
| FR4.7 | Close positions | P1 |

### FR5: Data Nodes
| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | Get quote (LTP, OHLC) | P0 |
| FR5.2 | Get market depth | P1 |
| FR5.3 | Get positions/holdings | P1 |
| FR5.4 | Get option chain | P1 |
| FR5.5 | Get historical data | P1 |

### FR6: Utility Nodes
| ID | Requirement | Priority |
|----|-------------|----------|
| FR6.1 | Variable (set/get/math operations) | P0 |
| FR6.2 | Delay (wait N seconds) | P1 |
| FR6.3 | HTTP request (external API) | P1 |
| FR6.4 | Telegram alert | P1 |
| FR6.5 | Log message | P0 |
| FR6.6 | Math expression | P1 |

### FR7: Webhook System
| ID | Requirement | Priority |
|----|-------------|----------|
| FR7.1 | Unique webhook URL per workflow | P0 |
| FR7.2 | Secret-based authentication | P0 |
| FR7.3 | Symbol injection from payload | P1 |
| FR7.4 | Regenerate token/secret | P1 |

### FR8: Scheduling
| ID | Requirement | Priority |
|----|-------------|----------|
| FR8.1 | Daily at specific time (IST) | P0 |
| FR8.2 | Weekly on specific days | P1 |
| FR8.3 | Interval (every N minutes) | P1 |
| FR8.4 | One-time at datetime | P2 |
| FR8.5 | Persist jobs across restarts | P0 |

### FR9: Execution
| ID | Requirement | Priority |
|----|-------------|----------|
| FR9.1 | Execute nodes sequentially | P0 |
| FR9.2 | Conditional branching (yes/no paths) | P0 |
| FR9.3 | Variable interpolation ({{var}}) | P0 |
| FR9.4 | Execution logging | P0 |
| FR9.5 | Prevent concurrent execution | P0 |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Node execution time | < 100ms per node |
| Max nodes per workflow | 100 |
| Max concurrent workflows | 50 |
| Webhook response time | < 1 second |

## Database Schema

```sql
flow_workflows (
  id INTEGER PRIMARY KEY,
  name VARCHAR,
  description TEXT,
  nodes JSON,           -- ReactFlow node array
  edges JSON,           -- ReactFlow edge array
  is_active BOOLEAN,
  webhook_token VARCHAR UNIQUE,
  webhook_secret VARCHAR,
  webhook_enabled BOOLEAN,
  webhook_auth_type VARCHAR,  -- "payload" or "url"
  schedule_job_id VARCHAR,
  api_key VARCHAR,
  created_at DATETIME,
  updated_at DATETIME
)

flow_workflow_executions (
  id INTEGER PRIMARY KEY,
  workflow_id INTEGER FK,
  status VARCHAR,       -- pending, running, completed, failed
  started_at DATETIME,
  completed_at DATETIME,
  logs JSON,            -- [{time, message, level}]
  error TEXT
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/flow/api/workflows` | GET | List all workflows |
| `/flow/api/workflows` | POST | Create workflow |
| `/flow/api/workflows/<id>` | GET | Get workflow |
| `/flow/api/workflows/<id>` | PUT | Update workflow |
| `/flow/api/workflows/<id>` | DELETE | Delete workflow |
| `/flow/api/workflows/<id>/execute` | POST | Manual execution |
| `/flow/api/workflows/<id>/activate` | POST | Activate (schedule) |
| `/flow/api/workflows/<id>/deactivate` | POST | Deactivate |
| `/flow/api/workflows/<id>/executions` | GET | Execution history |
| `/flow/api/workflows/<id>/webhook` | GET | Webhook info |

## Related Documentation

| Document | Description |
|----------|-------------|
| [Node Reference](./flow-node-reference.md) | Complete list of 50+ nodes |
| [Node Creation Guide](./flow-node-creation.md) | How to create new nodes |
| [UI Components](./flow-ui-components.md) | React components guide |
| [Execution Engine](./flow-execution.md) | Backend execution details |

## Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `blueprints/flow.py` | Web routes and workflow API | - |
| `services/flow_executor_service.py` | Main execution engine | ~1940 |
| `services/flow_openalgo_client.py` | OpenAlgo API wrapper for nodes | - |
| `services/flow_scheduler_service.py` | APScheduler integration | - |
| `services/flow_price_monitor_service.py` | Price alert monitoring | - |
| `database/flow_db.py` | SQLAlchemy models (workflows, executions) | - |
| `frontend/src/pages/flow/FlowEditor.tsx` | React Flow canvas | - |
| `frontend/src/pages/flow/FlowIndex.tsx` | Workflow list page | - |
| `frontend/src/components/flow/nodes/*.tsx` | 53 node implementations | - |
| `frontend/src/components/flow/panels/*.tsx` | ConfigPanel, NodePalette, ExecutionLog | - |

## Success Metrics

| Metric | Target |
|--------|--------|
| Workflows created | 100+ |
| Execution success rate | > 99% |
| Avg nodes per workflow | 5-10 |



---

# FILE: docs\prd\historify-api-reference.md

# Historify API Reference

Complete API documentation for the Historify historical data management feature.

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/historify/watchlist` | GET | List watchlist symbols |
| `/api/v1/historify/watchlist` | POST | Add symbol to watchlist |
| `/api/v1/historify/watchlist` | DELETE | Remove symbol from watchlist |
| `/api/v1/historify/download` | POST | Start data download |
| `/api/v1/historify/jobs` | GET | List download jobs |
| `/api/v1/historify/jobs/<id>` | GET | Get job details |
| `/api/v1/historify/jobs/<id>/pause` | POST | Pause job |
| `/api/v1/historify/jobs/<id>/resume` | POST | Resume job |
| `/api/v1/historify/jobs/<id>/cancel` | POST | Cancel job |
| `/api/v1/historify/ohlcv` | GET | Query OHLCV data |
| `/api/v1/historify/export` | GET | Export data to file |
| `/api/v1/historify/catalog` | GET | Get data catalog |
| `/api/v1/historify/fno/underlyings` | GET | List F&O underlyings |
| `/api/v1/historify/fno/expiries` | GET | Get expiry dates |
| `/api/v1/historify/fno/strikes` | GET | Get option strikes |

---

## Watchlist Endpoints

### List Watchlist

Get all symbols in the watchlist.

```http
GET /api/v1/historify/watchlist
```

**Response:**

```json
{
  "status": "success",
  "watchlist": [
    {
      "id": 1,
      "symbol": "SBIN",
      "exchange": "NSE",
      "display_name": "State Bank of India",
      "instrument_type": "EQ",
      "lot_size": 1,
      "added_at": "2024-01-15T09:00:00"
    },
    {
      "id": 2,
      "symbol": "NIFTY24JAN18000CE",
      "exchange": "NFO",
      "display_name": "NIFTY 18000 CE Jan 2024",
      "instrument_type": "OPT",
      "expiry": "2024-01-25",
      "strike": 18000,
      "option_type": "CE",
      "lot_size": 50,
      "added_at": "2024-01-15T10:00:00"
    }
  ]
}
```

### Add to Watchlist

Add a symbol to the watchlist.

```http
POST /api/v1/historify/watchlist
Content-Type: application/json
```

**Body:**

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Symbol added to watchlist",
  "watchlist_item": {
    "id": 3,
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "display_name": "Reliance Industries Ltd",
    "instrument_type": "EQ",
    "lot_size": 1
  }
}
```

### Bulk Add to Watchlist

Add multiple symbols at once.

```http
POST /api/v1/historify/watchlist/bulk
Content-Type: application/json
```

**Body:**

```json
{
  "symbols": [
    {"symbol": "SBIN", "exchange": "NSE"},
    {"symbol": "HDFC", "exchange": "NSE"},
    {"symbol": "INFY", "exchange": "NSE"}
  ]
}
```

**Response:**

```json
{
  "status": "success",
  "added": 3,
  "skipped": 0,
  "message": "3 symbols added to watchlist"
}
```

### Remove from Watchlist

Remove a symbol from the watchlist.

```http
DELETE /api/v1/historify/watchlist
Content-Type: application/json
```

**Body:**

```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Symbol removed from watchlist"
}
```

---

## Download Endpoints

### Start Download

Start a data download job.

```http
POST /api/v1/historify/download
Content-Type: application/json
```

**Body:**

```json
{
  "symbols": [
    {"symbol": "SBIN", "exchange": "NSE"},
    {"symbol": "RELIANCE", "exchange": "NSE"}
  ],
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "interval": "1m"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbols` | array | Yes | Symbols to download |
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |
| `interval` | string | No | Data interval: `1m`, `D` (default: `1m`) |
| `incremental` | boolean | No | Only download missing data (default: `true`) |

**Response:**

```json
{
  "status": "success",
  "job_id": 123,
  "message": "Download job created",
  "job": {
    "id": 123,
    "status": "pending",
    "total_items": 2,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "interval": "1m"
  }
}
```

### Download Watchlist

Download data for all watchlist symbols.

```http
POST /api/v1/historify/download/watchlist
Content-Type: application/json
```

**Body:**

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "interval": "1m"
}
```

**Response:**

```json
{
  "status": "success",
  "job_id": 124,
  "message": "Download job created for 25 watchlist symbols"
}
```

---

## Job Management Endpoints

### List Jobs

Get all download jobs.

```http
GET /api/v1/historify/jobs
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter by status |
| `limit` | int | 20 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response:**

```json
{
  "status": "success",
  "jobs": [
    {
      "id": 123,
      "job_name": "Equity Download",
      "status": "running",
      "total_items": 25,
      "completed_items": 10,
      "failed_items": 1,
      "created_at": "2024-01-15T10:00:00",
      "started_at": "2024-01-15T10:00:05"
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

### Get Job Details

Get detailed information for a specific job.

```http
GET /api/v1/historify/jobs/<job_id>
```

**Response:**

```json
{
  "status": "success",
  "job": {
    "id": 123,
    "job_name": "Equity Download",
    "status": "running",
    "total_items": 25,
    "completed_items": 10,
    "failed_items": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "interval": "1m",
    "created_at": "2024-01-15T10:00:00",
    "items": [
      {
        "symbol": "SBIN",
        "exchange": "NSE",
        "status": "completed",
        "records_downloaded": 9375
      },
      {
        "symbol": "HDFC",
        "exchange": "NSE",
        "status": "downloading",
        "records_downloaded": 0
      },
      {
        "symbol": "INFY",
        "exchange": "NSE",
        "status": "failed",
        "error_message": "No data available"
      }
    ]
  }
}
```

### Pause Job

```http
POST /api/v1/historify/jobs/<job_id>/pause
```

**Response:**

```json
{
  "status": "success",
  "message": "Job paused"
}
```

### Resume Job

```http
POST /api/v1/historify/jobs/<job_id>/resume
```

**Response:**

```json
{
  "status": "success",
  "message": "Job resumed"
}
```

### Cancel Job

```http
POST /api/v1/historify/jobs/<job_id>/cancel
```

**Response:**

```json
{
  "status": "success",
  "message": "Job cancelled"
}
```

---

## Query Endpoints

### Get OHLCV Data

Query stored OHLCV data.

```http
GET /api/v1/historify/ohlcv
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | Yes | Trading symbol |
| `exchange` | string | Yes | Exchange code |
| `interval` | string | No | Data interval (default: `D`) |
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |

**Supported Intervals:**

| Interval | Description | Storage |
|----------|-------------|---------|
| `1m` | 1 minute | Stored |
| `5m` | 5 minutes | Computed from 1m |
| `15m` | 15 minutes | Computed from 1m |
| `30m` | 30 minutes | Computed from 1m |
| `1h` | 1 hour | Computed from 1m |
| `D` | Daily | Stored |

**Response:**

```json
{
  "status": "success",
  "symbol": "SBIN",
  "exchange": "NSE",
  "interval": "D",
  "data": [
    {
      "timestamp": "2024-01-02T00:00:00",
      "open": 620.50,
      "high": 625.00,
      "low": 618.25,
      "close": 623.75,
      "volume": 15000000
    },
    {
      "timestamp": "2024-01-03T00:00:00",
      "open": 624.00,
      "high": 630.00,
      "low": 622.00,
      "close": 628.50,
      "volume": 18000000
    }
  ],
  "count": 2
}
```

### Export Data

Export data to file.

```http
GET /api/v1/historify/export
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | Yes | Trading symbol |
| `exchange` | string | Yes | Exchange code |
| `interval` | string | No | Data interval (default: `D`) |
| `start_date` | string | Yes | Start date |
| `end_date` | string | Yes | End date |
| `format` | string | No | Output format: `csv`, `parquet` (default: `csv`) |

**Response:**

Returns file download with appropriate MIME type.

---

## Data Catalog Endpoints

### Get Catalog

Get available data ranges.

```http
GET /api/v1/historify/catalog
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol` | string | No | Filter by symbol |
| `exchange` | string | No | Filter by exchange |

**Response:**

```json
{
  "status": "success",
  "catalog": [
    {
      "symbol": "SBIN",
      "exchange": "NSE",
      "interval": "1m",
      "first_date": "2023-01-01",
      "last_date": "2024-01-15",
      "record_count": 93750
    },
    {
      "symbol": "SBIN",
      "exchange": "NSE",
      "interval": "D",
      "first_date": "2020-01-01",
      "last_date": "2024-01-15",
      "record_count": 1000
    }
  ]
}
```

---

## F&O Discovery Endpoints

### List Underlyings

Get available F&O underlyings.

```http
GET /api/v1/historify/fno/underlyings
```

**Response:**

```json
{
  "status": "success",
  "underlyings": [
    {"symbol": "NIFTY", "exchange": "NFO", "lot_size": 50},
    {"symbol": "BANKNIFTY", "exchange": "NFO", "lot_size": 15},
    {"symbol": "FINNIFTY", "exchange": "NFO", "lot_size": 40},
    {"symbol": "RELIANCE", "exchange": "NFO", "lot_size": 250}
  ]
}
```

### Get Expiry Dates

Get available expiry dates for underlying.

```http
GET /api/v1/historify/fno/expiries
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `underlying` | string | Yes | Underlying symbol (e.g., NIFTY) |

**Response:**

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "expiries": [
    {"date": "2024-01-25", "type": "weekly"},
    {"date": "2024-02-01", "type": "weekly"},
    {"date": "2024-02-29", "type": "monthly"},
    {"date": "2024-03-28", "type": "monthly"}
  ]
}
```

### Get Option Strikes

Get available strikes for an expiry.

```http
GET /api/v1/historify/fno/strikes
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `underlying` | string | Yes | Underlying symbol |
| `expiry` | string | Yes | Expiry date (YYYY-MM-DD) |

**Response:**

```json
{
  "status": "success",
  "underlying": "NIFTY",
  "expiry": "2024-01-25",
  "strikes": [
    {"strike": 21000, "ce_symbol": "NIFTY24JAN21000CE", "pe_symbol": "NIFTY24JAN21000PE"},
    {"strike": 21050, "ce_symbol": "NIFTY24JAN21050CE", "pe_symbol": "NIFTY24JAN21050PE"},
    {"strike": 21100, "ce_symbol": "NIFTY24JAN21100CE", "pe_symbol": "NIFTY24JAN21100PE"}
  ]
}
```

### Download Option Chain

Download data for all strikes of an expiry.

```http
POST /api/v1/historify/fno/download-chain
Content-Type: application/json
```

**Body:**

```json
{
  "underlying": "NIFTY",
  "expiry": "2024-01-25",
  "start_date": "2024-01-15",
  "end_date": "2024-01-25",
  "interval": "1m"
}
```

**Response:**

```json
{
  "status": "success",
  "job_id": 125,
  "message": "Download job created for 120 option contracts"
}
```

---

## WebSocket Events

### Progress Updates

Connect to WebSocket for real-time job progress.

```javascript
const socket = io('/historify');

socket.on('historify_progress', (data) => {
    console.log(`Job ${data.job_id}: ${data.percent}%`);
    console.log(`Current: ${data.current_symbol}`);
});

socket.on('historify_complete', (data) => {
    console.log(`Job ${data.job_id} completed`);
    console.log(`Downloaded: ${data.total_records} records`);
});

socket.on('historify_error', (data) => {
    console.error(`Job ${data.job_id} error: ${data.message}`);
});
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SYMBOL_NOT_FOUND` | 404 | Symbol doesn't exist |
| `INVALID_DATE_RANGE` | 400 | Invalid or reversed date range |
| `NO_DATA_AVAILABLE` | 404 | No data for requested range |
| `JOB_NOT_FOUND` | 404 | Download job not found |
| `JOB_NOT_RUNNING` | 409 | Cannot pause/cancel non-running job |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many API requests |
| `BROKER_ERROR` | 500 | Error from broker API |

## Related Documentation

| Document | Description |
|----------|-------------|
| [Historify PRD](./historify.md) | Product requirements |
| [Data Model](./historify-data-model.md) | DuckDB schema |
| [Download Engine](./historify-download-engine.md) | Bulk download management |



---

# FILE: docs\prd\historify-data-model.md

# Historify Data Model

Complete documentation for DuckDB schema and data model used in Historify.

## Overview

Historify uses DuckDB for efficient columnar storage of historical OHLCV data with on-the-fly timeframe aggregation.

## Why DuckDB?

| Feature | DuckDB | SQLite |
|---------|--------|--------|
| Columnar storage | Yes (OLAP optimized) | No (row-based) |
| Compression | Excellent (~10x) | Minimal |
| Analytical queries | Very fast | Slower |
| Time-series aggregation | Built-in | Manual |
| File size per 1M candles | ~50MB | ~500MB |

## Database Location

```
openalgo/
└── db/
    └── historify.duckdb    # Historical data storage
```

## Schema Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         historify.duckdb                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐     ┌────────────────────┐                         │
│  │    market_data     │     │     watchlist      │                         │
│  │    (OHLCV data)    │     │   (tracked syms)   │                         │
│  └────────────────────┘     └────────────────────┘                         │
│                                                                              │
│  ┌────────────────────┐     ┌────────────────────┐                         │
│  │   download_jobs    │     │    job_items       │                         │
│  │   (bulk jobs)      │     │  (per-symbol)      │                         │
│  └────────────────────┘     └────────────────────┘                         │
│                                                                              │
│  ┌────────────────────┐     ┌────────────────────┐                         │
│  │  symbol_metadata   │     │   data_catalog     │                         │
│  │   (F&O info)       │     │  (date ranges)     │                         │
│  └────────────────────┘     └────────────────────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Table Definitions

### market_data

Primary table for storing OHLCV candles.

```sql
CREATE TABLE market_data (
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    interval VARCHAR NOT NULL,     -- '1m', 'D'
    timestamp TIMESTAMP NOT NULL,
    open DOUBLE NOT NULL,
    high DOUBLE NOT NULL,
    low DOUBLE NOT NULL,
    close DOUBLE NOT NULL,
    volume BIGINT NOT NULL,
    oi BIGINT,                     -- Open Interest (F&O only)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, exchange, interval, timestamp)
);

-- Indexes for fast querying
CREATE INDEX idx_market_data_symbol ON market_data(symbol, exchange);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX idx_market_data_interval ON market_data(interval);
```

### watchlist

Tracked symbols for data management.

```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    display_name VARCHAR,
    token VARCHAR,                  -- Broker token ID
    lot_size INTEGER DEFAULT 1,
    tick_size DOUBLE DEFAULT 0.05,
    instrument_type VARCHAR,        -- EQ, FUT, OPT, IDX
    expiry DATE,                    -- For F&O
    strike DOUBLE,                  -- For Options
    option_type VARCHAR,            -- CE, PE
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, exchange, user_id)
);
```

### download_jobs

Bulk download job tracking.

```sql
CREATE TABLE download_jobs (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    job_name VARCHAR,
    status VARCHAR DEFAULT 'pending',  -- pending, running, paused, completed, failed
    total_items INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    start_date DATE,
    end_date DATE,
    interval VARCHAR DEFAULT '1m',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
```

### job_items

Per-symbol status within a bulk job.

```sql
CREATE TABLE job_items (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES download_jobs(id),
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',  -- pending, downloading, completed, failed, skipped
    records_downloaded INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_job_items_job ON job_items(job_id);
```

### symbol_metadata

F&O symbol metadata cache.

```sql
CREATE TABLE symbol_metadata (
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    underlying VARCHAR,             -- For derivatives
    expiry DATE,
    strike DOUBLE,
    option_type VARCHAR,            -- CE, PE
    lot_size INTEGER,
    tick_size DOUBLE,
    token VARCHAR,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, exchange)
);
```

### data_catalog

Tracks available data ranges per symbol.

```sql
CREATE TABLE data_catalog (
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    interval VARCHAR NOT NULL,
    first_date DATE NOT NULL,
    last_date DATE NOT NULL,
    record_count BIGINT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (symbol, exchange, interval)
);
```

## Data Operations

### Insert OHLCV Data

```python
def insert_ohlcv(conn, symbol, exchange, interval, data):
    """Insert OHLCV data with upsert logic"""
    conn.execute("""
        INSERT INTO market_data (symbol, exchange, interval, timestamp, open, high, low, close, volume, oi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, exchange, interval, timestamp)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            oi = EXCLUDED.oi
    """, [
        symbol, exchange, interval,
        data['timestamp'], data['open'], data['high'],
        data['low'], data['close'], data['volume'], data.get('oi')
    ])
```

### Query OHLCV Data

```python
def get_ohlcv(conn, symbol, exchange, interval, start_date, end_date):
    """Retrieve OHLCV data for date range"""
    result = conn.execute("""
        SELECT timestamp, open, high, low, close, volume, oi
        FROM market_data
        WHERE symbol = ?
          AND exchange = ?
          AND interval = ?
          AND timestamp >= ?
          AND timestamp <= ?
        ORDER BY timestamp
    """, [symbol, exchange, interval, start_date, end_date])

    return result.fetchdf()  # Returns pandas DataFrame
```

### Aggregate Timeframes On-The-Fly

```python
def aggregate_timeframe(conn, symbol, exchange, target_interval, start_date, end_date):
    """
    Aggregate 1-minute data to higher timeframes.
    Supported: 5m, 15m, 30m, 1h from 1m base data.
    """
    interval_minutes = {
        '5m': 5, '15m': 15, '30m': 30, '1h': 60
    }

    minutes = interval_minutes.get(target_interval)
    if not minutes:
        raise ValueError(f"Unsupported interval: {target_interval}")

    result = conn.execute("""
        SELECT
            time_bucket(INTERVAL ? MINUTES, timestamp) AS timestamp,
            FIRST(open) AS open,
            MAX(high) AS high,
            MIN(low) AS low,
            LAST(close) AS close,
            SUM(volume) AS volume,
            LAST(oi) AS oi
        FROM market_data
        WHERE symbol = ?
          AND exchange = ?
          AND interval = '1m'
          AND timestamp >= ?
          AND timestamp <= ?
        GROUP BY time_bucket(INTERVAL ? MINUTES, timestamp)
        ORDER BY timestamp
    """, [minutes, symbol, exchange, start_date, end_date, minutes])

    return result.fetchdf()
```

## Indexing Strategy

### Primary Queries

| Query Type | Index Used |
|------------|------------|
| Single symbol date range | `idx_market_data_symbol` |
| All symbols for date | `idx_market_data_timestamp` |
| Specific interval only | `idx_market_data_interval` |

### Query Performance

| Operation | Data Size | Expected Time |
|-----------|-----------|---------------|
| Single day, 1 symbol | ~375 rows | < 10ms |
| 1 year daily, 1 symbol | ~250 rows | < 5ms |
| 1 year 1m, 1 symbol | ~93,750 rows | < 50ms |
| Aggregation (1m → 1h) | 1 year | < 100ms |

## Data Storage Estimates

### Per Candle Storage

| Field | Size (bytes) |
|-------|--------------|
| symbol | ~10 |
| exchange | ~4 |
| interval | ~2 |
| timestamp | 8 |
| OHLCV | 40 |
| oi | 8 |
| **Total (uncompressed)** | ~72 |
| **Compressed** | ~15-20 |

### Storage Projections

| Scenario | Raw Size | Compressed |
|----------|----------|------------|
| 100 symbols × 1 year × 1m | ~2.7 GB | ~500 MB |
| 100 symbols × 1 year × D | ~1.8 MB | ~400 KB |
| 1000 symbols × 1 year × D | ~18 MB | ~4 MB |

## Data Integrity

### Duplicate Prevention

```sql
-- Unique constraint prevents duplicates
PRIMARY KEY (symbol, exchange, interval, timestamp)

-- Upsert pattern updates existing records
ON CONFLICT DO UPDATE SET ...
```

### Gap Detection

```python
def detect_gaps(conn, symbol, exchange, interval, start_date, end_date):
    """Detect missing data gaps"""
    result = conn.execute("""
        WITH expected_times AS (
            SELECT generate_series(
                ?::TIMESTAMP,
                ?::TIMESTAMP,
                INTERVAL '1 minute'
            ) AS timestamp
        ),
        actual_times AS (
            SELECT timestamp
            FROM market_data
            WHERE symbol = ? AND exchange = ? AND interval = ?
        )
        SELECT e.timestamp
        FROM expected_times e
        LEFT JOIN actual_times a ON e.timestamp = a.timestamp
        WHERE a.timestamp IS NULL
          AND EXTRACT(HOUR FROM e.timestamp) >= 9
          AND EXTRACT(HOUR FROM e.timestamp) < 16
    """, [start_date, end_date, symbol, exchange, interval])

    return result.fetchdf()
```

## Export Functions

### Export to CSV

```python
def export_to_csv(conn, symbol, exchange, interval, start_date, end_date, filepath):
    """Export data to CSV file"""
    conn.execute("""
        COPY (
            SELECT timestamp, open, high, low, close, volume, oi
            FROM market_data
            WHERE symbol = ?
              AND exchange = ?
              AND interval = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY timestamp
        ) TO ? (HEADER, DELIMITER ',')
    """, [symbol, exchange, interval, start_date, end_date, filepath])
```

### Export to Parquet

```python
def export_to_parquet(conn, symbol, exchange, interval, start_date, end_date, filepath):
    """Export data to Parquet file"""
    conn.execute("""
        COPY (
            SELECT timestamp, open, high, low, close, volume, oi
            FROM market_data
            WHERE symbol = ?
              AND exchange = ?
              AND interval = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY timestamp
        ) TO ? (FORMAT PARQUET)
    """, [symbol, exchange, interval, start_date, end_date, filepath])
```

### Export to DataFrame

```python
def to_dataframe(conn, symbol, exchange, interval, start_date, end_date):
    """Return data as pandas DataFrame"""
    result = conn.execute("""
        SELECT timestamp, open, high, low, close, volume, oi
        FROM market_data
        WHERE symbol = ? AND exchange = ? AND interval = ?
          AND timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp
    """, [symbol, exchange, interval, start_date, end_date])

    return result.fetchdf()
```

## Connection Management

```python
import duckdb
from contextlib import contextmanager

DATABASE_PATH = 'db/historify.duckdb'

@contextmanager
def get_connection():
    """Get DuckDB connection with context manager"""
    conn = duckdb.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with get_connection() as conn:
    df = get_ohlcv(conn, 'SBIN', 'NSE', '1m', '2024-01-01', '2024-01-31')
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Historify PRD](./historify.md) | Product requirements |
| [Download Engine](./historify-download-engine.md) | Bulk download management |
| [API Reference](./historify-api-reference.md) | Complete API documentation |



---

# FILE: docs\prd\historify-download-engine.md

# Historify Download Engine

Complete documentation for the bulk download job management system.

## Overview

The download engine handles data retrieval from broker APIs with rate limiting, job tracking, and progress reporting.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Download Request                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  POST /api/v1/historify/download                                        ││
│  │  {symbols: [...], start_date, end_date, interval}                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Job Manager                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  1. Create download_job record (status: pending)                        ││
│  │  2. Create job_items for each symbol                                    ││
│  │  3. Queue job for execution                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Download Worker (Background Thread)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  For each job_item:                                                     ││
│  │    1. Check rate limiter                                                ││
│  │    2. Fetch data from broker API                                        ││
│  │    3. Transform to standard format                                      ││
│  │    4. Insert into DuckDB                                                ││
│  │    5. Update job_item status                                            ││
│  │    6. Emit progress via WebSocket                                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────┐ ┌───────────────┐
│   Broker API      │ │   DuckDB      │ │   WebSocket   │
│   (Rate Limited)  │ │   Storage     │ │   Progress    │
└───────────────────┘ └───────────────┘ └───────────────┘
```

## Job States

```
┌─────────┐
│ pending │ ──▶ Job created, waiting to start
└────┬────┘
     │
     ▼
┌─────────┐
│ running │ ──▶ Actively downloading data
└────┬────┘
     │
     ├───────────────┐
     ▼               ▼
┌─────────┐     ┌────────┐
│ paused  │     │ failed │ ──▶ Unrecoverable error
└────┬────┘     └────────┘
     │
     ▼
┌───────────┐
│ completed │ ──▶ All items processed
└───────────┘
```

## Job Item States

| State | Description |
|-------|-------------|
| `pending` | Waiting to be processed |
| `downloading` | Currently fetching data |
| `completed` | Successfully downloaded |
| `failed` | Download failed (with error) |
| `skipped` | Skipped (e.g., no data available) |

## Download Worker

### Worker Loop

```python
class DownloadWorker:
    def __init__(self):
        self._running = False
        self._current_job = None
        self._rate_limiter = RateLimiter(requests_per_second=5)

    def start(self):
        """Start the download worker thread"""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Main worker loop"""
        while self._running:
            # Get next pending job
            job = self._get_next_job()

            if job:
                self._process_job(job)
            else:
                time.sleep(1)  # Wait for new jobs

    def _process_job(self, job):
        """Process a single download job"""
        self._current_job = job
        job.status = 'running'
        job.started_at = datetime.now()
        db.session.commit()

        # Get pending items
        items = JobItem.query.filter_by(
            job_id=job.id,
            status='pending'
        ).all()

        for item in items:
            if not self._running or job.status == 'paused':
                break

            self._process_item(job, item)

        # Update job status
        if job.status != 'paused':
            failed = JobItem.query.filter_by(job_id=job.id, status='failed').count()
            job.status = 'failed' if failed == len(items) else 'completed'
            job.completed_at = datetime.now()
            db.session.commit()

        self._current_job = None
```

### Item Processing

```python
def _process_item(self, job, item):
    """Process a single job item (symbol)"""
    item.status = 'downloading'
    item.started_at = datetime.now()
    db.session.commit()

    try:
        # Wait for rate limiter
        self._rate_limiter.wait()

        # Fetch from broker
        data = self._fetch_from_broker(
            symbol=item.symbol,
            exchange=item.exchange,
            interval=job.interval,
            start_date=job.start_date,
            end_date=job.end_date
        )

        if data is None or len(data) == 0:
            item.status = 'skipped'
            item.error_message = 'No data available'
        else:
            # Insert into DuckDB
            self._insert_data(item.symbol, item.exchange, job.interval, data)
            item.status = 'completed'
            item.records_downloaded = len(data)

    except Exception as e:
        item.status = 'failed'
        item.error_message = str(e)
        logger.error(f"Download failed for {item.symbol}: {e}")

    finally:
        item.completed_at = datetime.now()
        job.completed_items += 1
        if item.status == 'failed':
            job.failed_items += 1
        db.session.commit()

        # Emit progress
        self._emit_progress(job)
```

## Rate Limiting

### Token Bucket Algorithm

```python
class RateLimiter:
    def __init__(self, requests_per_second=5):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()
        self._lock = threading.Lock()

    def wait(self):
        """Wait until a request token is available"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Add tokens based on elapsed time
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)

            if self.tokens < 1:
                # Wait for token to become available
                wait_time = (1 - self.tokens) / self.rate
                time.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
```

### Broker-Specific Limits

| Broker | Requests/Second | Daily Limit |
|--------|-----------------|-------------|
| Zerodha | 3 | 10,000 |
| Angel | 5 | Unlimited |
| Dhan | 10 | Unlimited |
| Fyers | 5 | 5,000 |

## Broker Data Fetching

### Universal Fetch Function

```python
def _fetch_from_broker(self, symbol, exchange, interval, start_date, end_date):
    """Fetch historical data from broker"""
    from broker.common.api import get_broker_api

    api = get_broker_api()

    # Map interval to broker format
    broker_interval = self._map_interval(interval)

    # Chunk large date ranges (broker limits)
    chunks = self._chunk_date_range(start_date, end_date)

    all_data = []
    for chunk_start, chunk_end in chunks:
        data = api.history(
            symbol=symbol,
            exchange=exchange,
            interval=broker_interval,
            start_date=chunk_start,
            end_date=chunk_end
        )

        if data:
            all_data.extend(data)

    return all_data
```

### Date Range Chunking

```python
def _chunk_date_range(self, start_date, end_date, max_days=90):
    """Split large date ranges into chunks"""
    chunks = []
    current = start_date

    while current < end_date:
        chunk_end = min(current + timedelta(days=max_days), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)

    return chunks
```

## Progress Reporting

### WebSocket Events

```python
def _emit_progress(self, job):
    """Emit job progress via WebSocket"""
    progress = {
        'job_id': job.id,
        'status': job.status,
        'total': job.total_items,
        'completed': job.completed_items,
        'failed': job.failed_items,
        'percent': (job.completed_items / job.total_items * 100) if job.total_items > 0 else 0,
        'current_symbol': self._current_item.symbol if self._current_item else None
    }

    socketio.emit('historify_progress', progress, namespace='/historify')
```

### Client-Side Listener

```javascript
socket.on('historify_progress', (data) => {
    console.log(`Job ${data.job_id}: ${data.percent}% complete`);
    console.log(`Downloading: ${data.current_symbol}`);

    // Update progress bar
    updateProgressBar(data.percent);

    if (data.status === 'completed') {
        showNotification('Download complete!');
    }
});
```

## Job Management

### Pause Job

```python
def pause_job(job_id):
    """Pause a running job"""
    job = DownloadJob.query.get(job_id)
    if job and job.status == 'running':
        job.status = 'paused'
        db.session.commit()
        return True, "Job paused"
    return False, "Job not running"
```

### Resume Job

```python
def resume_job(job_id):
    """Resume a paused job"""
    job = DownloadJob.query.get(job_id)
    if job and job.status == 'paused':
        job.status = 'pending'  # Worker will pick it up
        db.session.commit()

        # Wake up worker
        worker.notify()
        return True, "Job resumed"
    return False, "Job not paused"
```

### Cancel Job

```python
def cancel_job(job_id):
    """Cancel a job"""
    job = DownloadJob.query.get(job_id)
    if job and job.status in ['pending', 'running', 'paused']:
        job.status = 'cancelled'
        job.completed_at = datetime.now()
        db.session.commit()
        return True, "Job cancelled"
    return False, "Cannot cancel job"
```

## Incremental Downloads

### Check Existing Data

```python
def get_missing_ranges(symbol, exchange, interval, start_date, end_date):
    """Find missing date ranges for incremental download"""
    with get_connection() as conn:
        catalog = conn.execute("""
            SELECT first_date, last_date
            FROM data_catalog
            WHERE symbol = ? AND exchange = ? AND interval = ?
        """, [symbol, exchange, interval]).fetchone()

        if catalog is None:
            return [(start_date, end_date)]

        missing = []

        # Check if data before existing range needed
        if start_date < catalog['first_date']:
            missing.append((start_date, catalog['first_date'] - timedelta(days=1)))

        # Check if data after existing range needed
        if end_date > catalog['last_date']:
            missing.append((catalog['last_date'] + timedelta(days=1), end_date))

        return missing
```

### Smart Download

```python
def download_incremental(symbol, exchange, interval, start_date, end_date):
    """Download only missing data"""
    missing_ranges = get_missing_ranges(symbol, exchange, interval, start_date, end_date)

    for range_start, range_end in missing_ranges:
        data = fetch_from_broker(symbol, exchange, interval, range_start, range_end)
        insert_data(symbol, exchange, interval, data)

    # Update catalog
    update_data_catalog(symbol, exchange, interval)
```

## F&O Discovery

### Get Option Chain

```python
def download_option_chain(underlying, expiry, start_date, end_date):
    """Download all strikes for an expiry"""
    # Get available strikes
    strikes = get_option_strikes(underlying, expiry)

    symbols = []
    for strike in strikes:
        for option_type in ['CE', 'PE']:
            symbol = f"{underlying}{expiry.strftime('%d%b%y').upper()}{strike}{option_type}"
            symbols.append({
                'symbol': symbol,
                'exchange': 'NFO',
                'underlying': underlying,
                'strike': strike,
                'option_type': option_type,
                'expiry': expiry
            })

    # Create bulk download job
    return create_download_job(symbols, start_date, end_date, interval='1m')
```

## Error Handling

### Retry Logic

```python
def _fetch_with_retry(self, symbol, exchange, interval, start_date, end_date, max_retries=3):
    """Fetch with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return self._fetch_from_broker(symbol, exchange, interval, start_date, end_date)
        except RateLimitError:
            wait_time = 2 ** attempt
            logger.warning(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1)
```

### Error Categories

| Error Type | Handling |
|------------|----------|
| Rate limit | Exponential backoff |
| Network error | Retry 3 times |
| Invalid symbol | Skip, mark failed |
| No data | Skip, mark as skipped |
| Auth error | Fail job, notify user |

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `HISTORIFY_RATE_LIMIT` | 5 | Requests per second |
| `HISTORIFY_MAX_CHUNK_DAYS` | 90 | Max days per API request |
| `HISTORIFY_MAX_RETRIES` | 3 | Retry attempts on failure |
| `HISTORIFY_WORKER_THREADS` | 1 | Number of download workers |

## Related Documentation

| Document | Description |
|----------|-------------|
| [Historify PRD](./historify.md) | Product requirements |
| [Data Model](./historify-data-model.md) | DuckDB schema |
| [API Reference](./historify-api-reference.md) | Complete API documentation |



---

# FILE: docs\prd\historify.md

# PRD: Historify - Historical Data Management

> **Status:** 🚧 Beta - Implemented but evolving; some broker integrations may vary

## Overview

Historify is OpenAlgo's historical market data management system for downloading, storing, and exporting OHLCV data for backtesting and analysis.

## Problem Statement

Traders need historical data for:
- Backtesting strategies before live deployment
- Technical analysis and pattern recognition
- Training machine learning models

Current challenges:
- Broker APIs have rate limits and data retention limits
- No unified format across brokers
- Manual CSV downloads are tedious
- Large datasets require efficient storage

## Solution

A DuckDB-powered data management system that:
- Downloads historical data from connected broker
- Stores efficiently in columnar format
- Supports bulk downloads with job tracking
- Exports to CSV/Parquet for external tools

## Target Users

| User | Use Case |
|------|----------|
| Backtester | Download data for strategy validation |
| Quant Developer | Build ML models with historical data |
| Technical Analyst | Analyze patterns across timeframes |

## Functional Requirements

### FR1: Watchlist Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Add symbols to watchlist | P0 |
| FR1.2 | Bulk add from CSV | P1 |
| FR1.3 | Remove symbols | P0 |
| FR1.4 | Display symbol metadata | P2 |

### FR2: Data Download
| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Download single symbol | P0 |
| FR2.2 | Bulk download (batch jobs) | P0 |
| FR2.3 | Download entire option chains | P1 |
| FR2.4 | Incremental download (append new data) | P0 |
| FR2.5 | Job pause/resume/cancel | P1 |
| FR2.6 | Progress tracking via WebSocket | P1 |

### FR3: Data Storage
| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Store 1-minute and daily candles | P0 |
| FR3.2 | Compute other timeframes on-the-fly | P0 |
| FR3.3 | Store open interest for F&O | P1 |
| FR3.4 | Track data catalog (date ranges) | P0 |

### FR4: Data Export
| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | Export to CSV | P0 |
| FR4.2 | Export to Parquet | P1 |
| FR4.3 | Export to pandas DataFrame | P0 |
| FR4.4 | Filtered export (date range) | P1 |

### FR5: FNO Discovery
| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | List underlyings (NIFTY, BANKNIFTY, etc.) | P1 |
| FR5.2 | Get available expiries | P1 |
| FR5.3 | Get option chain for expiry | P1 |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Storage efficiency | < 100 bytes per candle |
| Query performance | < 100ms for 1 year daily data |
| Bulk download rate | 5 symbols/second |
| Max symbols per job | 10,000 |

## Database Schema

```
┌─────────────────────────────────────────────────┐
│                  DuckDB                          │
├─────────────────────────────────────────────────┤
│ market_data     - OHLCV candles                 │
│ watchlist       - Tracked symbols               │
│ download_jobs   - Bulk job tracking             │
│ job_items       - Per-symbol status             │
│ symbol_metadata - Expiry, strike, lotsize       │
└─────────────────────────────────────────────────┘
```

## Data Flow

```
User Request → Validate → Broker History API → Transform → DuckDB → Response
                              │
                              ▼
                    Rate Limiter (5 req/sec)
```

## Supported Intervals

| Stored | Computed from 1m |
|--------|------------------|
| 1m, D  | 5m, 15m, 30m, 1h |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/historify/watchlist` | GET/POST/DELETE | Watchlist CRUD |
| `/api/v1/historify/download` | POST | Start download |
| `/api/v1/historify/jobs` | GET/POST | Job management |
| `/api/v1/historify/ohlcv` | GET | Query data |
| `/api/v1/historify/export` | GET | Export to file |

## UI Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  Historify                                    [Download All] │
├─────────────────────────────────────────────────────────────┤
│  Watchlist (25 symbols)                                      │
│  ┌─────────┬──────────┬───────────┬──────────┬───────────┐  │
│  │ Symbol  │ Exchange │ Data From │ Data To  │ Actions   │  │
│  ├─────────┼──────────┼───────────┼──────────┼───────────┤  │
│  │ SBIN    │ NSE      │ 2023-01-01│ 2024-01-15│ [↓] [×]  │  │
│  │ RELIANCE│ NSE      │ 2023-01-01│ 2024-01-15│ [↓] [×]  │  │
│  └─────────┴──────────┴───────────┴──────────┴───────────┘  │
│                                                              │
│  Active Jobs                                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Job #123: Downloading NIFTY options (45/120)  [Pause]│   │
│  │ ████████████░░░░░░░░░░░░ 37%                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Data Model](./historify-data-model.md) | DuckDB schema and storage |
| [Download Engine](./historify-download-engine.md) | Bulk download job management |
| [API Reference](./historify-api-reference.md) | Complete API documentation |

## Key Files Reference

| File | Purpose |
|------|---------|
| `blueprints/historify.py` | Web routes and API endpoints |
| `services/historify_service.py` | Core download and storage logic |
| `services/historify_scheduler_service.py` | Bulk job scheduling |
| `db/historify.duckdb` | DuckDB database file |
| `frontend/src/pages/Historify.tsx` | React watchlist/download UI |
| `frontend/src/pages/HistorifyCharts.tsx` | React chart visualization |

> **Note:** Historical data availability depends on broker API capabilities. Not all brokers support the full date range or all intervals.

## Success Metrics

| Metric | Target |
|--------|--------|
| Data accuracy | 100% match with broker |
| Download success rate | > 95% |
| Storage growth | < 1GB per 1M candles |



---

# FILE: docs\prd\python-strategies-api-reference.md

# Python Strategies API Reference

Complete API documentation for the Python Strategy Hosting feature.

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/python/new` | POST | Upload new strategy |
| `/python/start/<id>` | POST | Start strategy execution |
| `/python/stop/<id>` | POST | Stop strategy execution |
| `/python/delete/<id>` | POST | Delete strategy and logs |
| `/python/schedule/<id>` | POST | Configure schedule |
| `/python/unschedule/<id>` | POST | Remove schedule |
| `/python/logs/<id>` | GET | View strategy logs |
| `/python/logs/<id>/stream` | GET | Stream logs (SSE) |
| `/python/api/strategies` | POST | List all strategies |
| `/python/api/status/<id>` | GET | Get strategy status |

---

## Upload Strategy

Upload a new Python strategy file.

### Request

```http
POST /python/new
Content-Type: multipart/form-data
```

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_file` | file | Yes | Python script file (.py) |
| `name` | string | No | Display name (defaults to filename) |

### Response

```json
{
  "status": "success",
  "strategy_id": "ema_crossover_20240115_093045",
  "message": "Strategy uploaded successfully"
}
```

### Errors

| Code | Message |
|------|---------|
| 400 | No file provided |
| 400 | Invalid file type (must be .py) |
| 500 | Failed to save strategy |

---

## Start Strategy

Start executing a strategy in a subprocess.

### Request

```http
POST /python/start/<strategy_id>
```

### Response

```json
{
  "status": "success",
  "strategy_id": "ema_crossover_20240115",
  "pid": 12345,
  "message": "Strategy started"
}
```

### Errors

| Code | Message |
|------|---------|
| 404 | Strategy not found |
| 409 | Strategy already running |
| 500 | Failed to start strategy |

---

## Stop Strategy

Stop a running strategy gracefully.

### Request

```http
POST /python/stop/<strategy_id>
```

### Response

```json
{
  "status": "success",
  "strategy_id": "ema_crossover_20240115",
  "message": "Strategy stopped"
}
```

### Errors

| Code | Message |
|------|---------|
| 404 | Strategy not found |
| 409 | Strategy not running |

---

## Delete Strategy

Delete strategy file and associated logs.

### Request

```http
POST /python/delete/<strategy_id>
```

### Response

```json
{
  "status": "success",
  "message": "Strategy deleted"
}
```

### Errors

| Code | Message |
|------|---------|
| 404 | Strategy not found |
| 409 | Cannot delete running strategy |

---

## Configure Schedule

Set automatic start/stop schedule for a strategy.

### Request

```http
POST /python/schedule/<strategy_id>
Content-Type: application/json
```

**Body:**

```json
{
  "start_time": "09:20",
  "stop_time": "15:15",
  "days": ["mon", "tue", "wed", "thu", "fri"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_time` | string | Yes | Start time in HH:MM format (IST) |
| `stop_time` | string | Yes | Stop time in HH:MM format (IST) |
| `days` | array | Yes | Days to run: `mon`, `tue`, `wed`, `thu`, `fri`, `sat` |

### Response

```json
{
  "status": "success",
  "strategy_id": "ema_crossover_20240115",
  "schedule": {
    "start_time": "09:20",
    "stop_time": "15:15",
    "days": ["mon", "tue", "wed", "thu", "fri"]
  },
  "message": "Schedule configured"
}
```

### Errors

| Code | Message |
|------|---------|
| 400 | Invalid time format |
| 400 | Invalid days |
| 404 | Strategy not found |

---

## Remove Schedule

Remove automatic schedule from a strategy.

### Request

```http
POST /python/unschedule/<strategy_id>
```

### Response

```json
{
  "status": "success",
  "message": "Schedule removed"
}
```

---

## View Logs

Get historical logs for a strategy.

### Request

```http
GET /python/logs/<strategy_id>
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lines` | int | 100 | Number of lines to return |
| `offset` | int | 0 | Skip first N lines |

### Response

```json
{
  "status": "success",
  "logs": [
    "2024-01-15 09:20:01 - Starting strategy for SBIN",
    "2024-01-15 09:20:02 - Fetched historical data",
    "2024-01-15 09:20:03 - EMA5=625.50, EMA10=623.20",
    "2024-01-15 09:20:03 - BUY signal generated"
  ]
}
```

---

## Stream Logs (SSE)

Real-time log streaming via Server-Sent Events.

### Request

```http
GET /python/logs/<strategy_id>/stream
Accept: text/event-stream
```

### Response

```
event: log
data: {"timestamp": "2024-01-15T09:20:01", "message": "Starting strategy"}

event: log
data: {"timestamp": "2024-01-15T09:20:02", "message": "BUY signal generated"}

event: status
data: {"status": "running", "pid": 12345}
```

### Event Types

| Event | Description |
|-------|-------------|
| `log` | New log line from strategy |
| `status` | Status change (running/stopped) |
| `error` | Error occurred |

---

## List Strategies

Get all strategies for current user.

### Request

```http
POST /python/api/strategies
```

### Response

```json
{
  "status": "success",
  "strategies": [
    {
      "strategy_id": "ema_crossover_20240115",
      "name": "EMA Crossover",
      "file_path": "ema_crossover.py",
      "is_running": true,
      "is_scheduled": true,
      "schedule_start": "09:20",
      "schedule_stop": "15:15",
      "schedule_days": ["mon", "tue", "wed", "thu", "fri"],
      "pid": 12345,
      "last_started": "2024-01-15T09:20:00",
      "last_stopped": null
    },
    {
      "strategy_id": "rsi_strategy_20240110",
      "name": "RSI Strategy",
      "file_path": "rsi_strategy.py",
      "is_running": false,
      "is_scheduled": false,
      "schedule_start": null,
      "schedule_stop": null,
      "schedule_days": [],
      "pid": null,
      "last_started": "2024-01-10T09:20:00",
      "last_stopped": "2024-01-10T15:15:00"
    }
  ]
}
```

---

## Get Strategy Status

Get detailed status for a specific strategy.

### Request

```http
GET /python/api/status/<strategy_id>
```

### Response

```json
{
  "status": "success",
  "strategy": {
    "strategy_id": "ema_crossover_20240115",
    "name": "EMA Crossover",
    "is_running": true,
    "pid": 12345,
    "uptime_seconds": 3600,
    "memory_mb": 45.2,
    "last_log": "BUY signal generated",
    "schedule": {
      "enabled": true,
      "start_time": "09:20",
      "stop_time": "15:15",
      "days": ["mon", "tue", "wed", "thu", "fri"],
      "next_start": "2024-01-16T09:20:00",
      "next_stop": "2024-01-15T15:15:00"
    }
  }
}
```

---

## Status Update Events (SSE)

Real-time status updates for all strategies.

### Request

```http
GET /python/api/status/stream
Accept: text/event-stream
```

### Response

```
event: status
data: {"strategy_id": "ema_crossover", "status": "running", "pid": 12345}

event: status
data: {"strategy_id": "rsi_strategy", "status": "stopped", "exit_code": 0}

event: schedule
data: {"strategy_id": "ema_crossover", "event": "scheduled_stop", "time": "15:15"}
```

---

## Strategy Script Environment

When a strategy runs, these environment variables are available:

| Variable | Description |
|----------|-------------|
| `OPENALGO_APIKEY` | API key for OpenAlgo requests |
| `OPENALGO_HOST` | OpenAlgo server URL |
| `PYTHONUNBUFFERED` | Set to '1' for real-time output |

### Using OpenAlgo SDK in Strategy

```python
#!/usr/bin/env python
import os
from openalgo import api

# Get credentials from environment
API_KEY = os.getenv('OPENALGO_APIKEY')
HOST = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')

# Initialize client
client = api(api_key=API_KEY, host=HOST)

# Place orders
response = client.placeorder(
    symbol='SBIN',
    exchange='NSE',
    action='BUY',
    quantity=100,
    price_type='MARKET',
    product='MIS'
)

# Get market data
quotes = client.quotes(symbol='SBIN', exchange='NSE')
print(f"LTP: {quotes['ltp']}")

# Get positions
positions = client.positions()
print(f"Open positions: {len(positions)}")
```

---

## Error Response Format

All endpoints return errors in this format:

```json
{
  "status": "error",
  "error_code": "STRATEGY_NOT_FOUND",
  "message": "Strategy with ID 'xyz' not found"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `STRATEGY_NOT_FOUND` | 404 | Strategy ID doesn't exist |
| `STRATEGY_RUNNING` | 409 | Cannot perform action on running strategy |
| `STRATEGY_NOT_RUNNING` | 409 | Strategy is not currently running |
| `INVALID_FILE_TYPE` | 400 | Uploaded file is not a Python script |
| `INVALID_SCHEDULE` | 400 | Schedule parameters are invalid |
| `SCHEDULE_NOT_FOUND` | 404 | Strategy has no schedule configured |
| `INTERNAL_ERROR` | 500 | Server-side error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/python/new` | 10 uploads/minute |
| `/python/start/*` | 30 requests/minute |
| `/python/logs/*` | 60 requests/minute |
| `/python/api/*` | 120 requests/minute |

## Related Documentation

| Document | Description |
|----------|-------------|
| [Python Strategies PRD](./python-strategies.md) | Product requirements |
| [Process Management](./python-strategies-process-management.md) | Subprocess handling |
| [Scheduling Guide](./python-strategies-scheduling.md) | Market-aware scheduling |



---

# FILE: docs\prd\python-strategies-process-management.md

# Python Strategies Process Management

Complete documentation for subprocess isolation, lifecycle management, and cross-platform support.

## Overview

Each Python strategy runs in an isolated subprocess with its own Python interpreter, environment, and resource limits.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Flask Application                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │              Python Strategy Blueprint (blueprints/python_strategy.py)  ││
│  │  • Strategy upload/delete                                                ││
│  │  • Start/stop control                                                    ││
│  │  • Schedule management                                                   ││
│  │  • Log streaming                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              │                                               │
│     ┌────────────────────────┼────────────────────────┐                     │
│     ▼                        ▼                        ▼                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Strategy 1  │    │  Strategy 2  │    │  Strategy 3  │                  │
│  │  Subprocess  │    │  Subprocess  │    │  Subprocess  │                  │
│  │  PID: 12345  │    │  PID: 12346  │    │  PID: 12347  │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Process Registry                                  ││
│  │  RUNNING_STRATEGIES = {                                                  ││
│  │    'strategy_1': {'process': <Process>, 'pid': 12345, 'start_time': ...}││
│  │    'strategy_2': {'process': <Process>, 'pid': 12346, 'start_time': ...}││
│  │  }                                                                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Process Creation

### Subprocess Launch

```python
def start_strategy(strategy_id):
    """Launch strategy in isolated subprocess"""
    config = get_strategy_config(strategy_id)
    script_path = Path(f"strategies/scripts/{config['file_path']}")

    # Prepare environment
    env = os.environ.copy()
    env['OPENALGO_APIKEY'] = get_api_key()
    env['OPENALGO_HOST'] = get_host_url()
    env['PYTHONUNBUFFERED'] = '1'  # Real-time output

    # Prepare log file
    log_file = Path(f"log/strategies/{strategy_id}.log")
    log_handle = open(log_file, 'a', buffering=1)

    # Platform-specific subprocess options
    kwargs = {
        'stdout': log_handle,
        'stderr': subprocess.STDOUT,
        'env': env,
        'cwd': str(Path.cwd()),
    }

    # Unix-specific: Create new process group
    if os.name != 'nt':
        kwargs['preexec_fn'] = os.setsid

    # Windows-specific: Create new process group
    else:
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP

    # Launch subprocess
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        **kwargs
    )

    # Register in process registry
    RUNNING_STRATEGIES[strategy_id] = {
        'process': process,
        'pid': process.pid,
        'log_handle': log_handle,
        'start_time': datetime.now(),
        'user_id': current_user_id
    }

    return process.pid
```

## Process Termination

### Graceful Shutdown

```python
def stop_strategy(strategy_id):
    """Stop strategy with graceful shutdown"""
    if strategy_id not in RUNNING_STRATEGIES:
        return False, "Strategy not running"

    info = RUNNING_STRATEGIES[strategy_id]
    process = info['process']

    try:
        if os.name != 'nt':
            # Unix: Send SIGTERM to process group
            pgid = os.getpgid(process.pid)
            os.killpg(pgid, signal.SIGTERM)
        else:
            # Windows: Send CTRL_BREAK_EVENT
            process.send_signal(signal.CTRL_BREAK_EVENT)

        # Wait for graceful termination (5 seconds)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if still running
            kill_strategy_force(strategy_id)

    except ProcessLookupError:
        # Process already terminated
        pass

    finally:
        cleanup_strategy(strategy_id)

    return True, "Strategy stopped"
```

### Force Kill

```python
def kill_strategy_force(strategy_id):
    """Force kill strategy and all child processes"""
    info = RUNNING_STRATEGIES.get(strategy_id)
    if not info:
        return

    process = info['process']

    try:
        if os.name != 'nt':
            # Unix: Kill entire process group
            pgid = os.getpgid(process.pid)
            os.killpg(pgid, signal.SIGKILL)
        else:
            # Windows: Kill process tree
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                capture_output=True
            )
    except Exception as e:
        logger.error(f"Force kill error: {e}")
```

### Child Process Handling

```
┌─────────────────────────────────────────────────────────────┐
│  Strategy Process (PID: 12345)                              │
│     │                                                        │
│     ├── Child Thread 1 (WebSocket listener)                 │
│     ├── Child Thread 2 (Data fetcher)                       │
│     └── Child Process (subprocess.run)                      │
│            └── Grandchild Process                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  On stop_strategy():                                         │
│  1. SIGTERM sent to process group (pgid)                    │
│  2. All processes in group receive signal                   │
│  3. Threads terminate when main process exits               │
│  4. Resources cleaned up                                     │
└─────────────────────────────────────────────────────────────┘
```

## Resource Limits (Unix)

```python
# Configurable via environment variable (default: 1024MB)
STRATEGY_MEMORY_LIMIT_MB = int(os.environ.get('STRATEGY_MEMORY_LIMIT_MB', '1024'))

def set_resource_limits():
    """Set resource limits for subprocess (Unix only)"""
    import resource

    # Memory limit: configurable (default 1024MB)
    memory_limit = STRATEGY_MEMORY_LIMIT_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

    # CPU time limit: No limit (managed by scheduler)
    # resource.setrlimit(resource.RLIMIT_CPU, (unlimited, unlimited))

    # File descriptor limit: 1024
    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
```

### Docker Thread Limiting

When running in Docker, numerical libraries (OpenBLAS, NumPy, Numba) must be thread-limited to prevent `RLIMIT_NPROC` exhaustion:

| Variable | Purpose | Recommended Value |
|----------|---------|-------------------|
| `OPENBLAS_NUM_THREADS` | OpenBLAS threads | 1-2 |
| `OMP_NUM_THREADS` | OpenMP threads | 1-2 |
| `MKL_NUM_THREADS` | Intel MKL threads | 1-2 |
| `NUMEXPR_NUM_THREADS` | NumExpr threads | 1-2 |
| `NUMBA_NUM_THREADS` | Numba JIT threads | 1-2 |

### Resource Scaling Guidelines

| Container RAM | Thread Limit | Memory/Strategy | Max Strategies |
|---------------|--------------|-----------------|----------------|
| 2GB | 1 | 256MB | 5 |
| 4GB | 2 | 512MB | 5-8 |
| 8GB+ | 2-4 | 1024MB | 10+ |

> **Reference**: [GitHub Issue #822](https://github.com/marketcalls/openalgo/issues/822) documents the RLIMIT_NPROC fix.

## Process Monitoring

### Health Check

```python
def check_strategy_health():
    """Check health of all running strategies"""
    for strategy_id, info in list(RUNNING_STRATEGIES.items()):
        process = info['process']

        # Check if process is alive
        poll_result = process.poll()

        if poll_result is not None:
            # Process has terminated
            exit_code = poll_result
            logger.warning(f"Strategy {strategy_id} terminated with code {exit_code}")

            # Update config
            update_strategy_status(strategy_id, 'stopped', exit_code)

            # Cleanup
            cleanup_strategy(strategy_id)

            # Emit status update
            emit_strategy_status(strategy_id, {
                'status': 'stopped',
                'exit_code': exit_code,
                'message': 'Process terminated unexpectedly'
            })
```

### Auto-Restart (Optional)

```python
def auto_restart_strategy(strategy_id):
    """Auto-restart crashed strategy if configured"""
    config = get_strategy_config(strategy_id)

    if config.get('auto_restart', False):
        restart_count = config.get('restart_count', 0)

        if restart_count < MAX_RESTARTS:
            logger.info(f"Auto-restarting {strategy_id}")
            time.sleep(5)  # Backoff
            start_strategy(strategy_id)
            update_config(strategy_id, {'restart_count': restart_count + 1})
```

## Log Streaming

### Real-Time Log Output

```python
def stream_logs(strategy_id):
    """Stream logs via SSE (Server-Sent Events)"""
    log_file = Path(f"log/strategies/{strategy_id}.log")

    def generate():
        with open(log_file, 'r') as f:
            # Start from end of file
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    yield f"data: {json.dumps({'log': line.strip()})}\n\n"
                else:
                    time.sleep(0.1)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache'}
    )
```

### Log File Management

```python
def setup_log_rotation(strategy_id):
    """Setup log rotation for strategy"""
    log_file = Path(f"log/strategies/{strategy_id}.log")

    # Rotate if > 10MB
    if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:
        # Rename to .log.1, .log.2, etc.
        for i in range(4, 0, -1):
            old_log = log_file.with_suffix(f'.log.{i}')
            new_log = log_file.with_suffix(f'.log.{i+1}')
            if old_log.exists():
                old_log.rename(new_log)

        log_file.rename(log_file.with_suffix('.log.1'))
```

## Directory Structure

```
openalgo/
├── strategies/
│   ├── scripts/                    # User-uploaded strategies
│   │   ├── ema_crossover.py
│   │   ├── rsi_strategy.py
│   │   └── my_custom_strategy.py
│   ├── examples/                   # Template strategies
│   │   ├── simple_ema.py
│   │   └── webhook_handler.py
│   └── strategy_configs.json       # Strategy configurations
├── log/
│   └── strategies/                 # Strategy output logs
│       ├── ema_crossover.log
│       ├── ema_crossover.log.1     # Rotated logs
│       └── rsi_strategy.log
└── blueprints/
    └── python_strategy.py          # Main blueprint (2500+ lines)
```

## Configuration Schema

```json
{
  "strategy_id": {
    "name": "EMA Crossover",
    "file_path": "ema_crossover.py",
    "user_id": "user123",
    "is_running": false,
    "is_scheduled": true,
    "schedule_start": "09:20",
    "schedule_stop": "15:15",
    "schedule_days": ["mon", "tue", "wed", "thu", "fri"],
    "last_started": "2024-01-15T09:20:00",
    "last_stopped": "2024-01-15T15:15:00",
    "pid": null,
    "manually_stopped": false,
    "auto_restart": false,
    "restart_count": 0
  }
}
```

## Cross-Platform Compatibility

| Feature | Unix (Linux/macOS) | Windows |
|---------|-------------------|---------|
| Process groups | `os.setsid()` | `CREATE_NEW_PROCESS_GROUP` |
| Graceful stop | `SIGTERM` to pgid | `CTRL_BREAK_EVENT` |
| Force kill | `SIGKILL` to pgid | `taskkill /F /T` |
| Resource limits | `resource.setrlimit()` | Not supported |
| Log streaming | Unbuffered stdout | Unbuffered stdout |

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `ProcessLookupError` | Process already terminated | Clean up registry |
| `PermissionError` | Cannot signal process | Check process ownership |
| `FileNotFoundError` | Script file missing | Re-upload strategy |
| `OSError: [Errno 12]` | Cannot fork (memory) | Free system resources |

### Recovery Procedures

```python
def recover_orphan_processes():
    """Find and clean up orphan strategy processes on startup"""
    for config_id, config in load_all_configs().items():
        if config.get('is_running') and config.get('pid'):
            pid = config['pid']

            # Check if process exists
            try:
                os.kill(pid, 0)  # Doesn't kill, just checks
                logger.info(f"Found running strategy: {config_id} (PID: {pid})")
                # Re-register in RUNNING_STRATEGIES if needed
            except ProcessLookupError:
                logger.warning(f"Orphan config found: {config_id}")
                update_strategy_status(config_id, 'stopped')
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Python Strategies PRD](./python-strategies.md) | Product requirements |
| [Scheduling Guide](./python-strategies-scheduling.md) | Market-aware scheduling |
| [API Reference](./python-strategies-api-reference.md) | Complete API documentation |



---

# FILE: docs\prd\python-strategies-scheduling.md

# Python Strategies Scheduling

Complete documentation for APScheduler integration and market-aware scheduling.

## Overview

Python strategies use APScheduler with IST timezone support to automatically start/stop based on market hours.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APScheduler                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │              BackgroundScheduler (timezone='Asia/Kolkata')              ││
│  │                                                                          ││
│  │  Jobs:                                                                   ││
│  │  ┌──────────────────────────────────────────────────────────────────┐  ││
│  │  │ daily_trading_day_check    │ Cron: 00:01 daily                   │  ││
│  │  │ market_hours_enforcer      │ Interval: 1 minute                  │  ││
│  │  │ strategy_start_job_<id>    │ Cron: 09:20 Mon-Fri                │  ││
│  │  │ strategy_stop_job_<id>     │ Cron: 15:15 Mon-Fri                │  ││
│  │  └──────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Market Calendar                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  is_trading_day()                                                        ││
│  │    │                                                                     ││
│  │    ├── Check weekday (Mon-Fri for equity)                               ││
│  │    │                                                                     ││
│  │    └── Check holiday calendar (NSE holidays)                            ││
│  │                                                                          ││
│  │  Market Hours:                                                           ││
│  │    NSE/BSE: 09:15 - 15:30                                               ││
│  │    MCX: 09:00 - 23:30                                                   ││
│  │    CDS: 09:00 - 17:00                                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Scheduler Initialization

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

IST = pytz.timezone('Asia/Kolkata')

# Initialize scheduler with IST timezone
SCHEDULER = BackgroundScheduler(timezone=IST)

def initialize_scheduler():
    """Initialize the strategy scheduler"""
    if not SCHEDULER.running:
        SCHEDULER.start()

        # Add daily trading day check (00:01 IST)
        SCHEDULER.add_job(
            func=daily_trading_day_check,
            trigger=CronTrigger(hour=0, minute=1, timezone=IST),
            id='daily_trading_day_check',
            replace_existing=True
        )

        # Add market hours enforcer (every minute)
        SCHEDULER.add_job(
            func=market_hours_enforcer,
            trigger='interval',
            minutes=1,
            id='market_hours_enforcer',
            replace_existing=True
        )
```

## Schedule Configuration

### User Interface

```
┌─────────────────────────────────────────────────────────────┐
│  Strategy Schedule Configuration                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Start Time: [09:20] IST                                    │
│  Stop Time:  [15:15] IST                                    │
│                                                              │
│  Trading Days:                                               │
│  [✓] Monday                                                  │
│  [✓] Tuesday                                                 │
│  [✓] Wednesday                                               │
│  [✓] Thursday                                                │
│  [✓] Friday                                                  │
│  [ ] Saturday                                                │
│                                                              │
│  [Save Schedule] [Clear Schedule]                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Schedule Storage

```json
{
  "my_strategy": {
    "is_scheduled": true,
    "schedule_start": "09:20",
    "schedule_stop": "15:15",
    "schedule_days": ["mon", "tue", "wed", "thu", "fri"]
  }
}
```

## Job Creation

### Add Schedule

```python
def schedule_strategy(strategy_id, start_time, stop_time, days):
    """Schedule strategy for automatic start/stop"""

    # Parse time
    start_hour, start_minute = map(int, start_time.split(':'))
    stop_hour, stop_minute = map(int, stop_time.split(':'))

    # Map day names to cron day-of-week values
    day_map = {
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
        'fri': 4, 'sat': 5, 'sun': 6
    }
    cron_days = ','.join(str(day_map[d]) for d in days)

    # Create start job
    SCHEDULER.add_job(
        func=scheduled_start_strategy,
        trigger=CronTrigger(
            hour=start_hour,
            minute=start_minute,
            day_of_week=cron_days,
            timezone=IST
        ),
        args=[strategy_id],
        id=f'strategy_start_{strategy_id}',
        replace_existing=True
    )

    # Create stop job
    SCHEDULER.add_job(
        func=scheduled_stop_strategy,
        trigger=CronTrigger(
            hour=stop_hour,
            minute=stop_minute,
            day_of_week=cron_days,
            timezone=IST
        ),
        args=[strategy_id],
        id=f'strategy_stop_{strategy_id}',
        replace_existing=True
    )

    # Update config
    update_strategy_config(strategy_id, {
        'is_scheduled': True,
        'schedule_start': start_time,
        'schedule_stop': stop_time,
        'schedule_days': days
    })
```

### Remove Schedule

```python
def unschedule_strategy(strategy_id):
    """Remove scheduled jobs for strategy"""

    # Remove start job
    if SCHEDULER.get_job(f'strategy_start_{strategy_id}'):
        SCHEDULER.remove_job(f'strategy_start_{strategy_id}')

    # Remove stop job
    if SCHEDULER.get_job(f'strategy_stop_{strategy_id}'):
        SCHEDULER.remove_job(f'strategy_stop_{strategy_id}')

    # Update config
    update_strategy_config(strategy_id, {
        'is_scheduled': False
    })
```

## Market Calendar Integration

### Trading Day Check

```python
def is_trading_day(date=None):
    """Check if given date is a trading day"""
    if date is None:
        date = datetime.now(IST).date()

    # Check weekday (0=Monday, 6=Sunday)
    if date.weekday() >= 5:  # Saturday or Sunday
        return False

    # Check against holiday calendar
    holidays = get_market_holidays(date.year)
    if date in holidays:
        return False

    return True
```

### Daily Trading Day Check

```python
def daily_trading_day_check():
    """
    Runs at 00:01 IST daily.
    Stops all scheduled strategies if not a trading day.
    """
    today = datetime.now(IST).date()

    if not is_trading_day(today):
        logger.info(f"Non-trading day detected: {today}")

        # Stop all scheduled strategies
        for strategy_id, config in get_all_configs().items():
            if config.get('is_scheduled') and config.get('is_running'):
                stop_strategy(strategy_id)
                update_strategy_config(strategy_id, {
                    'manually_stopped': False  # Will auto-resume
                })
```

### Market Hours Enforcer

```python
def market_hours_enforcer():
    """
    Runs every minute.
    Ensures strategies stop after market hours even if stop job missed.
    """
    now = datetime.now(IST)
    current_time = now.time()

    for strategy_id, config in get_all_configs().items():
        if not config.get('is_scheduled') or not config.get('is_running'):
            continue

        stop_time = datetime.strptime(config['schedule_stop'], '%H:%M').time()

        # If past stop time, stop strategy
        if current_time > stop_time:
            logger.info(f"Enforcing stop for {strategy_id} (past {stop_time})")
            stop_strategy(strategy_id)
```

## Holiday Calendar

### NSE Holiday List

```python
NSE_HOLIDAYS_2024 = [
    date(2024, 1, 26),   # Republic Day
    date(2024, 3, 8),    # Mahashivratri
    date(2024, 3, 25),   # Holi
    date(2024, 3, 29),   # Good Friday
    date(2024, 4, 11),   # Id-Ul-Fitr
    date(2024, 4, 14),   # Dr. Ambedkar Jayanti
    date(2024, 4, 17),   # Ram Navami
    date(2024, 4, 21),   # Mahavir Jayanti
    date(2024, 5, 1),    # Maharashtra Day
    date(2024, 5, 23),   # Buddha Purnima
    date(2024, 6, 17),   # Eid
    date(2024, 7, 17),   # Muharram
    date(2024, 8, 15),   # Independence Day
    date(2024, 10, 2),   # Mahatma Gandhi Jayanti
    date(2024, 11, 1),   # Diwali-Laxmi Pujan
    date(2024, 11, 15),  # Gurunanak Jayanti
    date(2024, 12, 25),  # Christmas
]

def get_market_holidays(year):
    """Get holiday list for given year"""
    if year == 2024:
        return NSE_HOLIDAYS_2024
    # Fetch from API or database for other years
    return fetch_holidays_from_api(year)
```

## Scheduled Job Handlers

### Scheduled Start

```python
def scheduled_start_strategy(strategy_id):
    """Handler for scheduled strategy start"""
    config = get_strategy_config(strategy_id)

    # Skip if manually stopped by user
    if config.get('manually_stopped'):
        logger.info(f"Skipping scheduled start for {strategy_id} (manually stopped)")
        return

    # Skip if not a trading day
    if not is_trading_day():
        logger.info(f"Skipping scheduled start for {strategy_id} (non-trading day)")
        return

    # Skip if already running
    if config.get('is_running'):
        logger.debug(f"Strategy {strategy_id} already running")
        return

    # Start the strategy
    logger.info(f"Scheduled start: {strategy_id}")
    start_strategy(strategy_id)
```

### Scheduled Stop

```python
def scheduled_stop_strategy(strategy_id):
    """Handler for scheduled strategy stop"""
    config = get_strategy_config(strategy_id)

    # Skip if not running
    if not config.get('is_running'):
        logger.debug(f"Strategy {strategy_id} not running")
        return

    # Stop the strategy
    logger.info(f"Scheduled stop: {strategy_id}")
    stop_strategy(strategy_id)

    # Mark as not manually stopped (for next day auto-start)
    update_strategy_config(strategy_id, {
        'manually_stopped': False
    })
```

## Job Persistence

### Restore Jobs on Restart

```python
def restore_scheduled_jobs():
    """Restore scheduled jobs from config after app restart"""
    for strategy_id, config in get_all_configs().items():
        if config.get('is_scheduled'):
            schedule_strategy(
                strategy_id,
                config['schedule_start'],
                config['schedule_stop'],
                config['schedule_days']
            )
            logger.info(f"Restored schedule for {strategy_id}")
```

### Scheduler State

```python
def get_scheduler_status():
    """Get current scheduler status"""
    jobs = []
    for job in SCHEDULER.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })

    return {
        'running': SCHEDULER.running,
        'job_count': len(jobs),
        'jobs': jobs
    }
```

## Timeline Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Monday, January 15, 2024 (Trading Day)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  00:01  daily_trading_day_check() runs                                      │
│         → Is Monday, not a holiday → Trading day confirmed                  │
│                                                                              │
│  09:20  strategy_start_ema_crossover job fires                              │
│         → scheduled_start_strategy('ema_crossover')                         │
│         → Strategy subprocess started (PID: 12345)                          │
│         → Log streaming begins                                               │
│                                                                              │
│  09:21  market_hours_enforcer() runs (every minute)                         │
│  09:22  market_hours_enforcer() runs                                        │
│  ...                                                                         │
│                                                                              │
│  15:15  strategy_stop_ema_crossover job fires                               │
│         → scheduled_stop_strategy('ema_crossover')                          │
│         → SIGTERM sent to process group                                     │
│         → Process terminated gracefully                                      │
│                                                                              │
│  15:16  market_hours_enforcer() runs                                        │
│         → Confirms all strategies stopped                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  Saturday, January 20, 2024 (Weekend)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  00:01  daily_trading_day_check() runs                                      │
│         → Is Saturday → NOT a trading day                                   │
│         → All scheduled strategies remain stopped                           │
│                                                                              │
│  09:20  strategy_start_ema_crossover job fires                              │
│         → scheduled_start_strategy('ema_crossover')                         │
│         → is_trading_day() returns False                                    │
│         → Start skipped                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Strategy doesn't start at scheduled time | Holiday or weekend | Check `is_trading_day()` |
| Strategy starts but immediately stops | Stop time before start time | Fix schedule config |
| Jobs lost after restart | `restore_scheduled_jobs()` not called | Add to app startup |
| Wrong timezone | System timezone mismatch | Ensure IST is used |

### Debug Commands

```python
# Check next run time for a job
job = SCHEDULER.get_job('strategy_start_ema_crossover')
print(f"Next run: {job.next_run_time}")

# List all jobs
for job in SCHEDULER.get_jobs():
    print(f"{job.id}: {job.next_run_time}")

# Check if scheduler is running
print(f"Scheduler running: {SCHEDULER.running}")
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Python Strategies PRD](./python-strategies.md) | Product requirements |
| [Process Management](./python-strategies-process-management.md) | Subprocess handling |
| [API Reference](./python-strategies-api-reference.md) | Complete API docs |



---

# FILE: docs\prd\python-strategies.md

# PRD: Python Strategies - Automated Strategy Execution

> **Status:** ✅ Stable - Fully implemented, production-ready

## Overview

Python Strategies enables traders to run custom Python trading algorithms within OpenAlgo, with process isolation, market-aware scheduling, and comprehensive lifecycle management.

## Problem Statement

Traders need to:
- Run Python-based trading strategies without infrastructure management
- Schedule strategies around market hours automatically
- Monitor strategy execution with real-time logs
- Safely test strategies in sandbox mode before live trading

## Solution

A subprocess-based strategy execution system that:
- Runs each strategy in isolated Python process
- Integrates with APScheduler for market-aware scheduling
- Provides real-time log streaming via SSE
- Supports Windows, Linux, and macOS

## Target Users

| User | Use Case |
|------|----------|
| Algo Developer | Run custom Python strategies |
| Technical Trader | Automate EMA/RSI-based systems |
| Quant Researcher | Deploy ML models for trading |

## Functional Requirements

### FR1: Strategy Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Upload Python strategy files | P0 |
| FR1.2 | Start/stop strategy execution | P0 |
| FR1.3 | Delete strategy and logs | P0 |
| FR1.4 | View strategy source code | P1 |
| FR1.5 | Edit strategy configuration | P1 |

### FR2: Process Isolation
| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Run each strategy in subprocess | P0 |
| FR2.2 | Resource limits (memory, CPU) | P1 |
| FR2.3 | Cross-platform support (Win/Linux/Mac) | P0 |
| FR2.4 | Graceful shutdown with SIGTERM | P0 |
| FR2.5 | Kill child processes on termination | P0 |

### FR3: Scheduling
| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Configure start/stop times (IST) | P0 |
| FR3.2 | Select trading days (Mon-Sat) | P0 |
| FR3.3 | Auto-stop on market holidays | P0 |
| FR3.4 | Auto-stop on weekends | P0 |
| FR3.5 | Resume on next trading day | P0 |
| FR3.6 | Persist schedules across restarts | P0 |

### FR4: Logging
| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | Capture stdout/stderr to log file | P0 |
| FR4.2 | Real-time log streaming (SSE) | P0 |
| FR4.3 | View historical logs | P0 |
| FR4.4 | Log file rotation | P1 |
| FR4.5 | Log cleanup (retention policy) | P1 |

### FR5: Status Monitoring
| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | Real-time status updates (SSE) | P0 |
| FR5.2 | Track running/stopped/error states | P0 |
| FR5.3 | Display uptime and PID | P1 |
| FR5.4 | Error message capture | P0 |

### FR6: API Integration
| ID | Requirement | Priority |
|----|-------------|----------|
| FR6.1 | OpenAlgo SDK available to strategies | P0 |
| FR6.2 | Environment variables for API key | P0 |
| FR6.3 | Access to all OpenAlgo API endpoints | P0 |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Strategy startup time | < 5 seconds |
| Log latency (event → display) | < 1 second |
| Max concurrent strategies | 50 (system-dependent) |
| Memory per strategy | 256MB-1024MB (configurable) |
| Scheduler precision | ±1 minute |

### Docker Resource Requirements

| Container RAM | Thread Limit | Memory/Strategy | Max Strategies |
|---------------|--------------|-----------------|----------------|
| 2GB | 1 | 256MB | 5 |
| 4GB | 2 | 512MB | 5-8 |
| 8GB+ | 2-4 | 1024MB | 10+ |

> **Note**: Thread limits (`OPENBLAS_NUM_THREADS`, etc.) prevent RLIMIT_NPROC exhaustion when using NumPy/SciPy/Numba. See [Issue #822](https://github.com/marketcalls/openalgo/issues/822).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Python Strategy Blueprint                    ││
│  │  Routes: /python/new, /start, /stop, /schedule, /logs   ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│     ┌─────────────────────┼─────────────────────┐           │
│     ▼                     ▼                     ▼           │
│  ┌──────────┐      ┌────────────┐       ┌────────────┐     │
│  │ Process  │      │ APScheduler│       │ SSE Server │     │
│  │ Manager  │      │  (IST TZ)  │       │  (Status)  │     │
│  └────┬─────┘      └─────┬──────┘       └────────────┘     │
│       │                  │                                  │
│       ▼                  ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Strategy Subprocess                   │  │
│  │  • Isolated Python process                            │  │
│  │  • Resource limits (Unix)                             │  │
│  │  • Unbuffered stdout for real-time logs               │  │
│  └───────────────────────┬──────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              OpenAlgo SDK (openalgo)                   │  │
│  │  • client.placesmartorder()                           │  │
│  │  • client.history()                                   │  │
│  │  • client.quotes()                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Strategy Template

```python
#!/usr/bin/env python
"""
Simple EMA Crossover Strategy Template
"""
import os
import time
from openalgo import api

# Configuration
API_KEY = os.getenv('OPENALGO_APIKEY')
HOST = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')
SYMBOL = 'SBIN'
EXCHANGE = 'NSE'
QUANTITY = 1

# Initialize client
client = api(api_key=API_KEY, host=HOST)

def calculate_ema(prices, period):
    """Calculate EMA for given prices"""
    multiplier = 2 / (period + 1)
    ema = [prices[0]]
    for price in prices[1:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return ema

def main():
    print(f"Starting strategy for {SYMBOL}")

    while True:
        try:
            # Fetch historical data
            df = client.history(
                symbol=SYMBOL,
                exchange=EXCHANGE,
                interval='5m',
                start_date='2024-01-01',
                end_date='2024-12-31'
            )

            # Calculate EMAs
            closes = df['close'].tolist()
            ema_fast = calculate_ema(closes, 5)[-1]
            ema_slow = calculate_ema(closes, 10)[-1]

            # Generate signal
            if ema_fast > ema_slow:
                print(f"BUY signal: EMA5={ema_fast:.2f} > EMA10={ema_slow:.2f}")
                client.placesmartorder(
                    strategy='ema_crossover',
                    symbol=SYMBOL,
                    action='BUY',
                    exchange=EXCHANGE,
                    price_type='MARKET',
                    product='MIS',
                    quantity=QUANTITY,
                    position_size=QUANTITY
                )
            elif ema_fast < ema_slow:
                print(f"SELL signal: EMA5={ema_fast:.2f} < EMA10={ema_slow:.2f}")
                client.placesmartorder(
                    strategy='ema_crossover',
                    symbol=SYMBOL,
                    action='SELL',
                    exchange=EXCHANGE,
                    price_type='MARKET',
                    product='MIS',
                    quantity=QUANTITY,
                    position_size=QUANTITY
                )

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(15)  # Check every 15 seconds

if __name__ == '__main__':
    main()
```

## Schedule Configuration

```json
{
  "strategy_id": "ema_crossover_20260115",
  "schedule": {
    "start_time": "09:20",
    "stop_time": "15:15",
    "days": ["mon", "tue", "wed", "thu", "fri"],
    "timezone": "Asia/Kolkata"
  }
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/python/new` | POST | Upload strategy file |
| `/python/start/<id>` | POST | Start execution |
| `/python/stop/<id>` | POST | Stop execution |
| `/python/delete/<id>` | POST | Delete strategy |
| `/python/schedule/<id>` | POST | Configure schedule |
| `/python/logs/<id>` | GET | View logs |
| `/python/api/strategies` | POST | List all strategies |

## Database Schema

```
strategy_configs.json (file-based)
├── strategy_id → {
│     name: str,
│     file_path: str,
│     user_id: str,
│     is_running: bool,
│     is_scheduled: bool,
│     schedule_start: 'HH:MM',
│     schedule_stop: 'HH:MM',
│     schedule_days: ['mon',...],
│     last_started: datetime,
│     last_stopped: datetime,
│     pid: int,
│     manually_stopped: bool
│   }
```

## Directory Structure

```
openalgo/
├── strategies/
│   ├── scripts/           # User-uploaded strategies
│   ├── examples/          # Template strategies
│   └── strategy_configs.json
├── log/
│   └── strategies/        # Strategy output logs
└── blueprints/
    └── python_strategy.py # Strategy hosting (~2680 lines)
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Process Management](./python-strategies-process-management.md) | Subprocess handling and lifecycle |
| [Scheduling Guide](./python-strategies-scheduling.md) | Market-aware scheduling with APScheduler |
| [API Reference](./python-strategies-api-reference.md) | Complete API documentation |

## Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `blueprints/python_strategy.py` | Main implementation with routes, process management, scheduling | ~2680 |
| `strategies/scripts/` | User-uploaded strategy Python files | - |
| `strategies/examples/` | Template strategies for users | - |
| `strategies/strategy_configs.json` | Strategy configuration storage | - |
| `log/strategies/` | Strategy execution log files | - |

> **Note:** React frontend for strategy management is served via the Flask backend's Jinja2 templates. The strategy list, upload, and log viewing are available at `/python/*` routes.

## Success Metrics

| Metric | Target |
|--------|--------|
| Strategy uptime | > 99% during market hours |
| Schedule accuracy | ±1 minute |
| Log delivery latency | < 1 second |
| Process isolation | 0 cross-contamination |



---

# FILE: docs\prd\README.md

# Product Requirements Document - OpenAlgo

## Product Overview

**Product Name:** OpenAlgo
**Version:** 2.0
**Type:** Open-source algorithmic trading platform

## Vision

Democratize algorithmic trading for Indian retail traders by providing a free, self-hosted platform that bridges trading signals from any source to any broker.

## Problem Statement

Indian retail traders face:
- Manual order execution delays (2-3 minutes per trade)
- No affordable automation solutions
- Vendor lock-in with expensive platforms
- Data privacy concerns with cloud-based solutions

## Solution

A unified API layer that:
- Connects 29 Indian brokers through standardized API
- Accepts signals from TradingView, Amibroker, Python, Excel, AI agents
- Executes orders in under 1 second
- Runs entirely on user's own infrastructure

## Target Users

| Segment | Needs |
|---------|-------|
| Retail Traders | Fast execution, low cost |
| Technical Traders | TradingView/Amibroker integration |
| Algo Developers | Python API, backtesting |
| Investment Advisors | Order approval workflow, audit trail |

## Core Features

| Feature | Priority | Status |
|---------|----------|--------|
| Multi-broker support (29) | P0 | Complete |
| REST API for orders | P0 | Complete |
| TradingView webhooks | P0 | Complete |
| Real-time WebSocket streaming | P0 | Complete |
| Sandbox testing mode | P0 | Complete |
| Visual workflow builder (Flow) | P1 | Complete |
| Historical data manager (Historify) | P1 | Complete |
| Action Center (order approval) | P1 | Complete |
| Python strategy execution | P1 | Complete |
| Telegram notifications | P2 | Complete |
| Options Analytics Tools (GEX, IV, OI) | P1 | Complete |
| Batched concurrent basket orders | P1 | Complete |
| Carry-forward position PnL tracking | P1 | Complete |
| NSE/BSE index symbol normalization | P1 | Complete |
| Health monitoring dashboard | P2 | Complete |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Order latency | < 500ms |
| Concurrent symbols | 3000+ |
| Uptime | 99.9% during market hours |
| Data privacy | 100% self-hosted |

## Success Metrics

- Active GitHub stars: 1000+
- Supported brokers: 29
- Daily order volume capability: 10,000+

## Detailed PRDs

### Flow - Visual Workflow Automation
- [Flow PRD](./flow.md) - Main product requirements
- [Node Creation Guide](./flow-node-creation.md) - How to create new nodes
- [Node Reference](./flow-node-reference.md) - Complete list of 50+ nodes
- [UI Components](./flow-ui-components.md) - React components guide
- [Execution Engine](./flow-execution.md) - Backend execution details

### Sandbox - Sandbox Trading Environment
- [Sandbox PRD](./sandbox.md) - Main product requirements
- [Architecture](./sandbox-architecture.md) - System architecture
- [Execution Engine](./sandbox-execution-engine.md) - Order matching engine
- [Margin System](./sandbox-margin-system.md) - Margin calculation and funds

### Python Strategies - Strategy Hosting
- [Python Strategies PRD](./python-strategies.md) - Main product requirements
- [Process Management](./python-strategies-process-management.md) - Subprocess handling
- [Scheduling](./python-strategies-scheduling.md) - Market-aware scheduling
- [API Reference](./python-strategies-api-reference.md) - Complete API documentation

### Historify - Historical Data Management
- [Historify PRD](./historify.md) - Main product requirements
- [Data Model](./historify-data-model.md) - DuckDB schema
- [Download Engine](./historify-download-engine.md) - Bulk download management
- [API Reference](./historify-api-reference.md) - Complete API documentation

### WebSocket Proxy
- [WebSocket Proxy PRD](./websocket-proxy.md) - Real-time market data streaming

### Event Bus - Order Side-Effect Decoupling
- [Event Bus PRD](./event-bus.md) - In-process pub/sub for order logging, SocketIO, and Telegram

### CI/CD Pipeline
- [CI/CD PRD](./ci-cd.md) - Main product requirements
- [Workflows Reference](./ci-cd-workflows.md) - Detailed job documentation
- [Security Scanning](./ci-cd-security.md) - Security tools and configuration
- [Local Development](./ci-cd-local-development.md) - Pre-commit setup guide



---

# FILE: docs\prd\remote-mcp.md

# PRD: Remote MCP (self-hosted, OAuth-authenticated)

> **Status:** Shipped in v2.0.1.0 on branch `remotemcp` (merged to `main`).
> **Owner:** @marketcalls
> **Related docs:** [`docs/userguide/remote-mcp.md`](../userguide/remote-mcp.md) (end-user guide), [`install/Remote-MCP-readme.md`](../../install/Remote-MCP-readme.md) (operator guide).

> **Supersedes:** the older "MCP is local-only" guidance that referred to `mcp/mcpserver.py`. The stdio transport remains local-only; Remote MCP is a parallel, opt-in HTTP/SSE transport gated behind `MCP_HTTP_ENABLED`. Both share the same 40 tools.

## Goal

Let a self-hosted OpenAlgo install expose its MCP tools to **hosted AI clients** (chatgpt.com, claude.ai, claude mobile) in addition to the existing local stdio integration with Claude Desktop / Cursor / Windsurf.

Concrete outcome: after running `install/install.sh` and pointing a domain at the server, the user can connect a hosted MCP client to `https://mcp.<their-domain>/mcp` and use OpenAlgo tools through standard OAuth.

## Non-goals

- **Multi-user**: a remote MCP server is still single-user, single-broker. The single OpenAlgo admin authorizes the client; there's no per-user MCP access.
- **Replacing the local stdio MCP**: stdio stays the default and works unchanged. Remote MCP is purely additive — opt-in, off by default.
- **A SaaS hosted MCP**: nothing runs on infrastructure operated by the OpenAlgo project.

## Coexistence requirement

Both transports must work:

| Transport | Use case | Auth | Default |
|---|---|---|---|
| stdio (`mcp/mcpserver.py`) | Claude Desktop, Cursor, Windsurf — local processes spawn the server | none (process boundary) | always available |
| HTTP+SSE (`blueprints/mcp_http.py`, new) | claude.ai, chatgpt.com, mobile, browser-side MCP clients | OAuth 2.1 + PKCE | opt-in via `MCP_HTTP_ENABLED=True` |

They share **one** tool registry. No tool is implemented twice.

## Architecture

```
                                                         ┌──────────────────────────┐
                                                         │  Hosted MCP client       │
                                                         │  (claude.ai / chatgpt)   │
                                                         └─────────┬────────────────┘
                                                                   │ OAuth + Bearer
                                                                   ▼
┌──────────────────────────────┐         ┌────────────────────────────────────────┐
│ Local MCP client              │         │ Flask app (Gunicorn + eventlet)        │
│ (Claude Desktop / Cursor)     │         │                                        │
└────────────┬──────────────────┘         │  ┌─────────────────────────────────┐   │
             │ stdio                       │  │ blueprints/mcp_oauth.py         │   │
             ▼                             │  │   /.well-known/* (discovery)    │   │
┌──────────────────────────────┐           │  │   /oauth/register (DCR)         │   │
│ mcp/mcpserver.py             │           │  │   /oauth/authorize              │   │
│   if __name__ == "__main__"  │           │  │   /oauth/token                  │   │
│   → mcp.run("stdio")          │           │  │   /oauth/revoke                 │   │
└────────────┬──────────────────┘           │  └─────────────────────────────────┘   │
             │                              │                                        │
             ▼                              │  ┌─────────────────────────────────┐   │
        ┌────────────────────────────────┐  │  │ blueprints/mcp_http.py          │   │
        │ mcp/tool_registry.py            │  │  │   POST /mcp (JSON-RPC dispatch) │   │
        │   mcp = FastMCP("openalgo")     │◀─┼──│   GET  /mcp (SSE stream)        │   │
        │   @mcp.tool()                   │  │  └─────────────────────────────────┘   │
        │   def place_order(...): ...     │  │                                        │
        │   ... (all tools)               │  │  ┌─────────────────────────────────┐   │
        └─────────────────────────────────┘  │  │ Existing service layer + REST   │   │
                                             │  │ /api/v1/* (broker calls)        │   │
                                             │  └─────────────────────────────────┘   │
                                             └────────────────────────────────────────┘
```

### Tool registry sharing

`mcp/mcpserver.py` is split into:

- **`mcp/tool_registry.py`** — the `FastMCP` instance and every `@mcp.tool()` definition. Pure logic, no transport concerns. Importable.
- **`mcp/mcpserver.py`** — kept as the stdio entry point. After the split it shrinks to ~10 lines: import the registry, `mcp.run()`. Existing `claude_desktop_config.json` users see no change.
- **`blueprints/mcp_http.py`** — imports the same `mcp` instance and exposes a JSON-RPC dispatcher over Flask routes. Bypasses FastMCP's HTTP server so it stays under our (eventlet-friendly) WSGI stack.

### Authentication flow

```
1. claude.ai POSTs to /mcp without a token.
2. Server returns 401 + WWW-Authenticate: Bearer
   resource_metadata="https://mcp.example/.well-known/oauth-protected-resource"
3. claude.ai fetches resource metadata, then authorization-server metadata.
4. claude.ai POSTs to /oauth/register (DCR) with its redirect_uri.
5. claude.ai redirects user to /oauth/authorize?... (with PKCE challenge).
6. User logs in to OpenAlgo (existing session) and approves scopes on a consent page.
7. Server redirects back to claude.ai with an authorization code.
8. claude.ai POSTs the code + verifier to /oauth/token; receives access + refresh.
9. claude.ai retries POST /mcp with Authorization: Bearer <access_token>.
10. Server validates JWT signature + scope; dispatches to tool registry.
```

### User authentication at the consent step

**Decision: the OpenAlgo dashboard login (username + password + TOTP), not the API key.**

There are two distinct credentials in play, which are easy to conflate:

| Credential | Who holds it | Where it's used in remote MCP |
|---|---|---|
| OpenAlgo login (username + password + TOTP) | Admin user, interactively at the browser | Gates `/oauth/authorize` — proves the human at the keyboard is the OpenAlgo admin and consents to grant the MCP client access |
| OpenAlgo API key | Server-side `.env` value | Used **inside** the tool implementations when they call back to `/api/v1/*` — the user never sees or enters it during OAuth |

The user-facing OAuth flow looks like:

```
1. claude.ai redirects to https://mcp.example/oauth/authorize?...
2. /oauth/authorize is gated by @check_session_validity:
   - If no valid session → standard OpenAlgo login page (username + password + TOTP)
   - On successful login → redirected back to the consent screen
3. Consent screen shows: "claude.ai wants: read:market, read:account [, write:orders]"
                         [Authorize]  [Deny]
4. Authorize → server emits authorization code → redirect back to claude.ai
```

Why login, not API key:

- **TOTP gate.** The login flow already enforces TOTP. API keys do not. Authorizing an order-placement client is exactly the moment a TOTP step is appropriate.
- **Right level of friction.** OAuth consent is a one-time interactive step. Pasting an API key on a consent screen is awkward and trains users to expose API keys in browsers.
- **Aligns with industry norm.** Kite, Google, GitHub, etc. all gate their OAuth `/authorize` with the same login the user uses for the dashboard, not with an API token.
- **Recovery story.** A user who loses their API key still has password+TOTP and can revoke MCP access; a user who loses password+TOTP would already be locked out of OpenAlgo entirely, so MCP is not a new dependency.

#### Fresh-auth requirement (MUST-HAVE for v1)

For sensitive scope grants, the existing session alone is not enough. Rules:

- **`read:*` only** — existing session sufficient. Click `Authorize` and proceed.
- **`write:orders`** — server requires a fresh TOTP within the last 60 seconds before showing the consent screen. If the user logged in 4 hours ago, they are re-prompted for TOTP only (not full password). Implemented via a `tot_verified_at` timestamp on the session.
- **Any scope, first-time client approval** (DCR client never approved before) — full re-auth: password + TOTP, regardless of session age. The first approval is the trust establishment step and deserves the friction.

#### `MCP_OAUTH_LOGIN_AUTH_LEVEL` config

| Value | Behavior |
|---|---|
| `session` | Any valid OpenAlgo session passes (least friction) |
| `totp` (**default**) | Fresh TOTP within 60s required for any `write:orders` grant |
| `password+totp` | Full re-auth on every `/authorize`, regardless of scope |

Default is `totp` — strikes the balance between UX and order-placement authority.

#### What about API key only?

If we ever want a non-interactive flow (e.g. headless test scripts), the API key path stays available via the existing `/api/v1/*` REST endpoints. **There is intentionally no MCP OAuth flow that accepts an API key as the user credential** — that would defeat the purpose of having an interactive consent step and lose the TOTP gate. CLI clients that want MCP access still go through the standard browser-based OAuth dance once; the resulting refresh token then enables headless use until it expires (30 days).

### Token model

| Token | Format | Storage | TTL | Notes |
|---|---|---|---|---|
| Access | RS256 JWT, signed with key in `keys/mcp_oauth_<kid>.pem` | none for **authentication** (stateless — verified by signature + `exp`); per-`jti` in-memory side-channels for rate limiting and write-idempotency tracking | **15 min** | Includes `scope`, `client_id`, `jti` |
| Refresh | opaque random | hashed with `API_KEY_PEPPER` in `oauth_db.OAuthRefreshToken` | **30 days**, single-use, rotated | Identical hashing to API keys |
| Authorization code | opaque random | in-memory (dict with TTL) | **60 sec** | PKCE-verified, single-use |

The access-token model is **stateless from the authentication perspective** — verifiers don't hit the DB, only the public JWK and the `exp` claim. The in-memory state described later (per-`jti` rate-limit window, last-1000 `request_id`s per token for write idempotency) is a side-channel for rate enforcement and replay protection, not for authentication. A token that survives `exp` is unusable regardless of the side-channel state.

### Scopes

Coarse, three-way split. Refining later as tools are added.

| Scope | Granted tools |
|---|---|
| `read:market` | quotes, depth, history, search, intervals, optionchain, optionsymbol |
| `read:account` | orderbook, tradebook, positionbook, holdings, funds, openposition, orderstatus |
| `write:orders` | place_order, place_smart_order, place_options_order, modify_order, cancel_order, cancel_all_orders, close_position, basket, split |

Each tool is annotated with its required scope in the registry. Token verification middleware enforces `scope` on every dispatch.

### Database

New file `database/oauth_db.py` with three tables in `db/openalgo.db`:

- `oauth_clients` — DCR-registered clients. Fields: `client_id`, `client_name`, `redirect_uris[]`, `created_at`, `approved` (bool, optional admin approval).
- `oauth_refresh_tokens` — `id`, `client_id`, `token_hash`, `scopes`, `created_at`, `expires_at`, `revoked_at`, `last_used_at`, `parent_token_id` (chain for rotation audit).
- `oauth_signing_keys` — `kid`, `algorithm`, `public_jwk`, `created_at`, `rotated_at`. Private key stays on disk under `keys/`.

Authorization codes are NOT persisted — kept in-memory with 60s TTL.

### Audit

Every MCP tool invocation logs to `log/mcp.jsonl`:

```json
{"ts": "...", "jti": "...", "client_id": "...", "scope": "write:orders",
 "tool": "place_order", "params_hash": "...", "duration_ms": 42, "outcome": "success"}
```

Params are NOT logged in full — only a SHA-256 hash for correlation. The actual order shows up in the existing trade logs anyway.

### Rate limits

Tighter than the regular API rate limits to protect order placement.

| Endpoint | Limit |
|---|---|
| `/oauth/register` (DCR) | 10/hour per IP |
| `/oauth/token` | 20/min per client_id |
| `POST /mcp` (read scopes) | 60/min per token |
| `POST /mcp` (write:orders) | 5/min per token |

## Security model — defense in depth

Exposing an order-placement surface to the public internet is fundamentally
high-risk: a stolen access token from a registered IP places real orders
that SEBI's static-IP rule cannot prevent. The defaults below are deliberately
restrictive — write tools are **off** by default even after MCP HTTP is
enabled. Users who want trading-via-MCP must consciously opt in twice.

### Defense layers

```
Internet → Cloudflare/WAF (recommended) → nginx → Flask
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 0: TLS │  (Let's Encrypt, HSTS preload)
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 1: IP  │  optional MCP_HTTP_IP_ALLOWLIST
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 2: CORS│  exact origin match
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 3: Rate│  per-IP, per-client, per-token
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 4: OAuth│ PKCE, JWT signature, exp, jti
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 5: Scope│ read-only vs write gates
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 6: Tool │ per-tool quantity caps,
                                  │  guards        │ confirmation, kill switch
                                  └───────┬───────┘
                                          ↓
                                  ┌───────────────┐
                                  │  Layer 7: Audit│ jsonl log + Telegram notify
                                  └───────────────┘
```

### MUST-HAVE for v1 (release blocker if any are missing)

1. **PKCE S256 only.** `code_challenge_method=plain` is rejected; only `S256` is advertised in discovery and accepted at the token endpoint.
2. **Refresh token rotation with reuse detection.** Each refresh token is single-use. If a revoked refresh token is presented, the entire token family (chain via `parent_token_id`) is immediately revoked — RFC 6749 §10.4 pattern. Forces an attacker who stole one refresh to lose all subsequent tokens the moment the legitimate client refreshes.
3. **Write tools off by default.** `MCP_OAUTH_WRITE_SCOPE_ENABLED=False` is the default. Even with `MCP_HTTP_ENABLED=True`, the `write:orders` scope is not advertised in discovery and any token request that asks for it returns `invalid_scope`. The admin must explicitly opt in by flipping the env var and restarting.
4. **DCR requires admin approval by default.** `MCP_OAUTH_REQUIRE_APPROVAL=True`. New DCR registrations land in `pending` state and cannot complete the OAuth flow until the admin approves them on `/admin/oauth-clients` (new admin tile). This stops the "anyone in the world can start an OAuth flow against your server" attack.
5. **Pre-flight refusal in debug mode.** If `FLASK_DEBUG=True` *and* `MCP_HTTP_ENABLED=True`, app startup fails with a clear error. Debug mode leaks tokens via `werkzeug` tracebacks and must never coexist with the MCP transport.
6. **Tokens hashed with `API_KEY_PEPPER`.** Refresh tokens never persist in plaintext. Same Argon2/HMAC pipeline as OpenAlgo API keys.
7. **Signing key on disk.** RS256 private key in `keys/mcp_oauth_signing.pem`, chmod `600`, owned by the OpenAlgo process user. Auto-generated by install scripts. Not in git, not in `.env`.
8. **Audit log for every tool call.** Append-only `log/mcp.jsonl`. Contains `ts`, `jti`, `client_id`, `tool`, `scope`, `params_hash` (SHA-256 of the JSON-canonical params), `duration_ms`, `outcome`, `request_ip`. Params are NOT logged in full — only hashed for correlation against the existing trade log.
9. **Telegram notification on every write tool call** when the existing Telegram bot is configured. The notification fires **before** the order goes to the broker so the admin gets a chance to see "MCP is about to place X" and revoke if surprising. Re-uses existing `services/telegram_bot_service.py`.
10. **Kill switch endpoint.** `POST /admin/mcp/disable` (admin-session-gated) atomically: sets a runtime flag that 503s every `/mcp` request, revokes all refresh tokens, dumps the in-memory access-token allowlist. One click stops the world without restarting Gunicorn.
11. **Per-tool rate limits.** Defaults: `5/min` for `write:orders`, `60/min` for `read:*`. Enforced per token (`jti`), not per IP — a single compromised token can't slip past by hopping IPs.
12. **Per-IP rate limits on auth endpoints.** `/oauth/register` 10/hour, `/oauth/token` 20/min, `/oauth/authorize` 30/min. These run *before* OAuth so brute-force / spray attacks fail fast.
13. **Exact `redirect_uri` match.** No wildcards, no path-prefix matching. The registered URI is compared character-by-character at both `/oauth/authorize` and `/oauth/token`.
14. **Strict CORS allowlist.** `Access-Control-Allow-Origin` is set only for origins in `MCP_HTTP_CORS_ORIGINS` (default: `https://claude.ai,https://chatgpt.com`). Pre-flight responses don't reveal the full allowlist on a mismatch — they just return without the CORS headers.
15. **Sensitive-data redaction.** Existing `SensitiveDataFilter` in `utils/logging.py` is extended to redact `Authorization: Bearer …`, `client_secret`, `code`, and `refresh_token` values from any log path the MCP code touches.
16. **Short access TTL.** 15 minutes. Refresh-only path forces revocation propagation within one TTL window.
17. **`kid` rotation support.** Two signing keys (`active` + `previous`) advertised in JWKS for one TTL window after rotation. Validation accepts either. Compromise response: drop `previous`, restart, force re-auth.
18. **Replay protection on writes.** Every JSON-RPC request with a `write:orders` scope must include a client-generated `request_id` (UUID). Server tracks the last 1000 `request_id`s per token in-memory; duplicates within the access-token window are rejected with `idempotency_replay`.

### SHOULD-HAVE for v1 (default-on, configurable)

19. **Optional IP allowlist for `/mcp`.** `MCP_HTTP_IP_ALLOWLIST=1.2.3.4,5.6.7.0/24`. When set, all MCP requests are rejected unless the source IP matches. Empty (default) = no IP filtering. Useful if the user's MCP client lives on a known fixed egress.
20. **Kill switch on session timeout.** *(Not yet implemented in v2.0.1.0.)* If the OpenAlgo admin hasn't logged in for the configurable session inactivity window (`MCP_INACTIVITY_REVOKE_DAYS`, default 7), all refresh tokens are revoked. A live admin must re-authorize the MCP client. Catches the "user forgot they enabled this" failure mode.
21. **Inbound order quantity cap.** *(Not yet implemented in v2.0.1.0.)* `MCP_MAX_ORDER_QTY` (default `0` = no cap). When set, any tool placing an order with `quantity > cap` is rejected at the dispatcher before reaching the broker.
22. **Confirmation token for high-value writes.** *(Not yet implemented in v2.0.1.0.)* Optional `MCP_CONFIRM_WRITES=True`. When set, write tools require an additional `confirm_token` parameter that the client obtains from a separate `/oauth/confirm-write` endpoint, which displays an admin consent prompt for that single tool call. Adds a per-trade human-in-the-loop step.
23. **Telegram-driven kill switch.** *(Not yet implemented in v2.0.1.0.)* If Telegram is configured, the user can reply `/mcp_disable` in the bot to trigger the same kill switch. Useful when away from the dashboard.

### NICE-TO-HAVE (deferred to v1.1)

24. **Anomaly detection** — flag and auto-disable on patterns like 100 orders in 1 minute, or sudden symbol changes outside historical norm.
25. **Geographic / ASN restrictions** — extend the existing IP-ban list to also work as an MCP-only allowlist with country / ASN granularity.
26. **mTLS option** — pre-shared client cert in addition to OAuth, for paranoid setups.
27. **Bot Management hooks** — explicit Cloudflare Turnstile challenge on `/oauth/authorize`.

### Threat → mitigation table

| Threat | Mitigation |
|---|---|
| Token theft → unauthorized order placement | (1) Write tools off by default, (3) 15-min access TTL, (11) per-token write rate limit `5/min`, (18) request_id replay protection, (9) Telegram notification fires before broker call, (10) one-click kill switch |
| DCR abuse: world-readable registration endpoint | (4) admin approval default-on; (12) per-IP `/oauth/register` rate limit `10/hour` |
| Refresh token replay | (2) single-use rotation + family revocation on re-use; refresh tokens stored hashed |
| Code interception | (1) PKCE S256 mandatory; (13) exact `redirect_uri` match |
| Open redirect | (13) exact match — no wildcards, no prefix |
| Cross-origin token exfil from compromised browser | (14) strict CORS allowlist; (3) short access TTL limits exfil window |
| Long-running tool starves event loop | Per-tool soft-timeout (5s reads / 30s writes); cooperative `eventlet.sleep(0)` between batches |
| Debug-mode catastrophic exposure | (5) pre-flight refusal — Flask refuses to start with both flags on |
| Signing key compromise | (17) `kid` rotation; private key chmod 600, in `keys/` |
| Compromised client_secret | DCR-issued secrets stored hashed; rotation via `/oauth/register/<client_id>` PUT |
| Forgotten enablement → token still valid months later | (20) inactivity-based revocation; (10) kill switch |
| Operator accident: admin enables MCP_HTTP but never realizes write is off | Documentation + post-install banner + admin Diagnostics page shows MCP status prominently |
| Quantity-based abuse (legit token, harmful trade) | (21) `MCP_MAX_ORDER_QTY`; (22) optional per-write confirmation |
| Eventlet single-worker DoS via slow MCP traffic | Per-token rate limits run *before* tool dispatch; SSE streams have idle timeouts |
| SEBI static-IP bypass | Not exploitable — broker calls still originate from registered server IP. The trust boundary is the admin's OAuth approval, not the IP. |
| Log-based credential leak | (15) `SensitiveDataFilter` extended for OAuth fields |
| Privilege escalation across scopes | Token signature includes `scope` claim; verifier rejects tools whose required scope isn't in the token's scope set |
| Compromised OpenAlgo admin password → MCP takeover | Same blast radius as compromised admin already. Mitigation is on the OpenAlgo side (Argon2, rate-limited login). MCP doesn't widen this. |
| Discovery endpoint leak of internal hostnames | Discovery returns only the configured `MCP_PUBLIC_URL`, never internal IPs |

### Configuration (`.sample.env`)

```bash
# === Remote MCP (HTTP + OAuth) ===
# Off by default. Local stdio MCP works without these.
MCP_HTTP_ENABLED = 'False'

# Public origin where the MCP HTTP transport is reachable.
# Used in OAuth discovery metadata. Must be HTTPS in production.
MCP_PUBLIC_URL = 'https://mcp.example.com'

# OAuth signing key (RS256). Auto-generated by install scripts.
MCP_OAUTH_SIGNING_KEY = 'keys/mcp_oauth_signing.pem'

# Require admin approval before a DCR client can complete OAuth.
# Recommended for production. When True, register puts the client in
# pending state visible at /admin/oauth-clients.
MCP_OAUTH_REQUIRE_APPROVAL = 'True'

# CORS allowlist for the MCP HTTP endpoint. Comma-separated.
MCP_HTTP_CORS_ORIGINS = 'https://claude.ai,https://chatgpt.com'

# Token TTLs (seconds). Sane defaults; only override for testing.
MCP_OAUTH_ACCESS_TTL = '900'      # 15 min
MCP_OAUTH_REFRESH_TTL = '2592000' # 30 days
MCP_OAUTH_CODE_TTL = '60'

# Per-token rate limits.
MCP_RATE_LIMIT_READ = '60 per minute'
MCP_RATE_LIMIT_WRITE = '5 per minute'
```

### Install integration

`install/install.sh` gains an optional MCP block:

```
[?] Enable remote MCP server (allows ChatGPT/Claude.ai to call OpenAlgo)? [y/N]
[?] MCP subdomain (e.g. mcp.yourdomain.com):
  - Generates RS256 signing key under keys/
  - Adds nginx server block with Let's Encrypt cert
  - Sets MCP_HTTP_ENABLED=True and MCP_PUBLIC_URL in .env
```

Defaults to **No**. The install scripts that already handle TLS (`install-docker-multi-custom-ssl.sh`, `change-domain.sh`) get matching support.

### Phased plan (one PR per phase)

| Phase | Scope | Branch state | Est |
|---|---|---|---|
| **1 — Foundation** *(this PR)* | PRD, scaffold blueprints, config keys, dependency add, tool-registry split skeleton | branch builds, no behavior change | — |
| **2 — OAuth server** | `mcp_oauth.py` with Authlib: discovery, DCR, authorize, token, revoke. DB models. Admin consent UI. No MCP transport yet. | OAuth flow demonstrably works against a CLI test client | ~1 wk |
| **3 — MCP HTTP transport** | `mcp_http.py` with JSON-RPC dispatcher reading the shared tool registry. Token validation middleware. SSE stream. Audit log. Rate limits. | claude.ai connector test passes end-to-end | ~1 wk |
| **4 — Install integration** | `install.sh` MCP block, nginx template, signing key generation, TLS via existing Let's Encrypt path | one-shot install on Ubuntu produces a working `https://mcp.<domain>/mcp` | ~3 days |
| **5 — Hardening + docs** | External security review, threat-model walkthrough, user docs, mention in README | ready to announce | ~3 days |

### Open questions

1. **Authlib vs hand-rolled** — Authlib brings ~600KB of dep weight but removes a category of crypto bugs. Default: Authlib. Will revisit if it conflicts with eventlet.
2. **Discovery URL shape** — RFC 8414 says `/.well-known/oauth-authorization-server`. MCP spec also references resource metadata at `/.well-known/oauth-protected-resource`. Implementing both.
3. **Per-tool re-auth for high-value writes** — should `place_order` require a token issued in the last 60s? Adds friction. Default: no re-auth, instead rely on rate limits + audit. Re-evaluate after security review.
4. **Single-tenant simplification** — DCR allows arbitrary client registration. For a single-user install we could short-circuit with one pre-approved client per OpenAlgo install. Default: keep DCR (matches MCP spec); add `MCP_OAUTH_REQUIRE_APPROVAL` for friction-on-demand.
5. **Mobile / native client UX** — claude.ai mobile follows the same OAuth flow but the redirect dance feels heavy. No special handling planned for v1.

### Out of scope for this branch

- ChatGPT custom GPTs / OpenAI's MCP support — same protocol, should "just work" but won't be explicitly tested in v1
- Multi-broker switching via MCP (the current OpenAlgo session ties one user to one broker)
- Streaming tool responses for very large reads (history, instruments) — v1 returns whole payloads



---

# FILE: docs\prd\sandbox-architecture.md

# Sandbox Architecture

Detailed architecture documentation for the Sandbox (Analyzer Mode) sandbox trading system.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  /api/v1/placeorder  │  /api/v1/positions  │  /api/v1/orders           ││
│  │  /api/v1/closeposi   │  /api/v1/holdings   │  /api/v1/cancelorder      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                              │ ANALYZER_MODE=True                            │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     sandbox_api.py Router                                ││
│  │         Routes to Sandbox managers instead of live broker                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SANDBOX CORE                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │ OrderManager  │  │PositionMgr   │  │ FundManager   │  │HoldingsMgr  │  │
│  │               │  │               │  │               │  │             │  │
│  │ • Validate    │  │ • Netting     │  │ • Margins     │  │ • T+1 Settl │  │
│  │ • Create      │  │ • MTM P&L     │  │ • Block/Free  │  │ • CNC→Hold  │  │
│  │ • Queue       │  │ • Close       │  │ • Credit/Debit│  │ • Sell Hold │  │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  └──────┬──────┘  │
│          │                  │                  │                  │         │
│          └──────────────────┼──────────────────┼──────────────────┘         │
│                             ▼                  ▼                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                       sandbox.db (SQLite)                                ││
│  │  sandbox_orders │ sandbox_positions │ sandbox_funds │ sandbox_holdings  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXECUTION ENGINE                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                WebSocket Execution Engine (Primary)                      ││
│  │  • Subscribes to real-time LTP via WebSocket proxy                      ││
│  │  • Immediate order matching on price updates                            ││
│  │  • Auto-fallback to polling if WebSocket unavailable                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                Polling Execution Engine (Fallback)                       ││
│  │  • Polls pending orders every 2 seconds                                 ││
│  │  • Fetches LTP from broker API                                          ││
│  │  • Matches orders sequentially                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SETTLEMENT & SQUARE-OFF                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │   Square-Off Manager    │  │    Settlement Jobs      │                   │
│  │   • MIS at 15:15 (NSE)  │  │    • T+1 at midnight    │                   │
│  │   • MIS at 23:30 (MCX)  │  │    • Expired F&O clean  │                   │
│  │   • Close at exchange   │  │    • Session boundary   │                   │
│  └─────────────────────────┘  └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Order Manager (`sandbox/order_manager.py`)

Handles all order operations with validation and margin checks.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `place_order()` | Create and validate new order |
| `cancel_order()` | Cancel pending order |
| `modify_order()` | Modify pending order parameters |
| `get_order_book()` | Retrieve all orders |
| `get_trade_book()` | Get executed trades |

**Order States:**

```
PENDING → TRIGGER_PENDING → COMPLETE
    ↓           ↓
 CANCELLED   REJECTED
```

**Validation Flow:**

```python
def place_order(symbol, exchange, action, quantity, product, price_type, ...):
    # 1. Validate symbol exists
    if not validate_symbol(symbol, exchange):
        raise InvalidSymbolError()

    # 2. Calculate required margin
    margin = calculate_margin(symbol, quantity, product, action)

    # 3. Check CNC sell from holdings
    if product == 'CNC' and action == 'SELL':
        available = position_qty + holdings_qty
        if quantity > available:
            raise InsufficientHoldingsError()

    # 4. Block margin for BUY or margin requirement
    if action == 'BUY' or product in ['MIS', 'NRML']:
        fund_manager.block_margin(margin)

    # 5. Create order record
    order = SandboxOrders(...)

    # 6. For MARKET orders, execute immediately
    if price_type == 'MARKET':
        execute_order(order, current_ltp)

    return order.order_id
```

### 2. Position Manager (`sandbox/position_manager.py`)

Manages position tracking with netting and MTM calculations.

**Position Netting Logic:**

```
Case 1: Same Direction (Adding to position)
  Current: LONG 100 @ 500
  New BUY: 50 @ 510
  Result: LONG 150 @ avg((100*500 + 50*510)/150) = 503.33

Case 2: Opposite Direction (Partial close)
  Current: LONG 100 @ 500
  New SELL: 50 @ 520
  Result: LONG 50 @ 500, Realized P&L: 50*(520-500) = +1000

Case 3: Opposite Direction (Close and reverse)
  Current: LONG 100 @ 500
  New SELL: 150 @ 520
  Result: SHORT 50 @ 520
         Realized P&L (close): 100*(520-500) = +2000
```

**MTM Calculation:**

```python
def calculate_mtm(position, current_ltp):
    """Real-time MTM P&L calculation"""
    if position.quantity > 0:  # LONG
        unrealized_pnl = (current_ltp - position.average_price) * position.quantity
    else:  # SHORT
        unrealized_pnl = (position.average_price - current_ltp) * abs(position.quantity)

    return position.realized_pnl + unrealized_pnl
```

### 3. Fund Manager (`sandbox/fund_manager.py`)

Tracks sandbox capital with margin blocking/release.

**Fund Structure:**

```python
class SandboxFunds:
    user_id: str
    available_balance: Decimal  # Default: 10,000,000 (1 Cr)
    used_margin: Decimal        # Blocked for open positions
    realized_pnl: Decimal       # Booked P&L from closed trades
```

**Margin Operations:**

| Operation | Effect |
|-----------|--------|
| `block_margin(amount)` | available - amount, used + amount |
| `release_margin(amount)` | available + amount, used - amount |
| `book_pnl(profit)` | available + profit, realized + profit |
| `book_pnl(loss)` | available - loss, realized - loss |

### 4. Holdings Manager (`sandbox/holdings_manager.py`)

Manages delivery holdings with T+1 settlement.

**Settlement Flow:**

```
Day T (Trading Day):
  09:15 - BUY CNC 100 SBIN @ 620
        → Creates CNC position (not holding yet)
        → Margin blocked: 62,000

Day T+1 (After Midnight):
  00:01 - T+1 Settlement Job runs
        → CNC position → Holdings conversion
        → Holdings record created
        → Margin transferred to holdings

Day T+1 (Trading Day):
  09:15 - Can now SELL from holdings
```

## Database Schema

### sandbox_orders

```sql
CREATE TABLE sandbox_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR NOT NULL,
    order_id VARCHAR UNIQUE NOT NULL,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    action VARCHAR NOT NULL,        -- BUY, SELL
    quantity INTEGER NOT NULL,
    product VARCHAR NOT NULL,       -- MIS, CNC, NRML
    price_type VARCHAR NOT NULL,    -- MARKET, LIMIT, SL, SL-M
    price DECIMAL(18,2),
    trigger_price DECIMAL(18,2),
    filled_quantity INTEGER DEFAULT 0,
    average_price DECIMAL(18,2),
    status VARCHAR DEFAULT 'PENDING',
    status_message TEXT,
    order_timestamp DATETIME,
    exchange_timestamp DATETIME,
    strategy VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
```

### sandbox_positions

```sql
CREATE TABLE sandbox_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    product VARCHAR NOT NULL,
    quantity INTEGER DEFAULT 0,
    average_price DECIMAL(18,2) DEFAULT 0,
    ltp DECIMAL(18,2),
    pnl DECIMAL(18,2) DEFAULT 0,
    realized_pnl DECIMAL(18,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    UNIQUE(user_id, symbol, exchange, product)
);
```

### sandbox_holdings

```sql
CREATE TABLE sandbox_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    average_price DECIMAL(18,2) NOT NULL,
    ltp DECIMAL(18,2),
    pnl DECIMAL(18,2) DEFAULT 0,
    pnl_percent DECIMAL(8,2) DEFAULT 0,
    settlement_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    UNIQUE(user_id, symbol, exchange)
);
```

### sandbox_funds

```sql
CREATE TABLE sandbox_funds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR UNIQUE NOT NULL,
    available_balance DECIMAL(18,2) DEFAULT 10000000,
    used_margin DECIMAL(18,2) DEFAULT 0,
    realized_pnl DECIMAL(18,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
```

## API Integration

All standard OpenAlgo API endpoints work seamlessly when Analyzer Mode is enabled:

```python
# In analyzer mode, these automatically route to sandbox
client.placeorder(...)      # → sandbox/order_manager.place_order()
client.positions()          # → sandbox/position_manager.get_positions()
client.holdings()           # → sandbox/holdings_manager.get_holdings()
client.funds()              # → sandbox/fund_manager.get_funds()
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Sandbox PRD](./sandbox.md) | Main product requirements |
| [Execution Engine](./sandbox-execution-engine.md) | Order matching details |
| [Margin System](./sandbox-margin-system.md) | Margin calculation rules |



---

# FILE: docs\prd\sandbox-execution-engine.md

# Sandbox Execution Engine

Complete documentation for the Sandbox order execution engine with WebSocket and polling modes.

## Overview

The execution engine matches pending orders against real-time market prices. Two execution modes are available:

| Mode | Performance | Requirement |
|------|-------------|-------------|
| WebSocket | Real-time (~50ms latency) | WebSocket proxy running |
| Polling | 2-second intervals | Broker API access |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Execution Thread Controller                           │
│                    sandbox/execution_thread.py                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  start_execution_engine(engine_type='websocket')                  │  │
│  │      │                                                             │  │
│  │      ├──▶ Check WebSocket proxy health                            │  │
│  │      │         │                                                   │  │
│  │      │         ├──▶ Healthy → Start WebSocket Engine              │  │
│  │      │         │                                                   │  │
│  │      │         └──▶ Unhealthy → Fallback to Polling Engine        │  │
│  │      │                                                             │  │
│  │      └──▶ engine_type='polling' → Start Polling Engine            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
┌───────────────────────────┐     ┌───────────────────────────┐
│   WebSocket Engine        │     │   Polling Engine          │
│   (Primary)               │     │   (Fallback)              │
│                           │     │                           │
│ • Subscribe to LTP stream │     │ • Poll every 2 seconds    │
│ • Instant order matching  │     │ • Fetch LTP from broker   │
│ • Event-driven execution  │     │ • Sequential matching     │
└───────────────────────────┘     └───────────────────────────┘
```

## WebSocket Execution Engine

Located in `sandbox/websocket_execution_engine.py`.

### Initialization

```python
def start_websocket_execution_engine():
    """Start WebSocket-based execution engine"""
    global _execution_engine

    if not _is_websocket_proxy_healthy():
        return False, "WebSocket proxy not available"

    _execution_engine = WebSocketExecutionEngine()
    _execution_engine.start()

    return True, "WebSocket execution engine started"
```

### Order Matching Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  WebSocket Message Handler                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Receive LTP Update: {symbol: "SBIN", ltp: 625.50}           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Find matching pending orders for symbol                      │
│     SELECT * FROM sandbox_orders                                 │
│     WHERE symbol = 'SBIN' AND status IN ('PENDING', 'TRIGGER')  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. For each order, check execution conditions                   │
│     • MARKET: Execute immediately at LTP                         │
│     • LIMIT BUY: Execute if LTP <= limit_price                  │
│     • LIMIT SELL: Execute if LTP >= limit_price                 │
│     • SL BUY: Trigger if LTP >= trigger_price                   │
│     • SL SELL: Trigger if LTP <= trigger_price                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Execute matched order                                        │
│     • Update order status to COMPLETE                            │
│     • Create trade record                                        │
│     • Update position (netting)                                  │
│     • Update funds (P&L booking)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Symbol Subscription

```python
def _subscribe_pending_symbols(self):
    """Subscribe to WebSocket for all symbols with pending orders"""
    pending_symbols = self._get_pending_order_symbols()

    for symbol, exchange in pending_symbols:
        self._websocket_client.subscribe(
            symbol=symbol,
            exchange=exchange,
            mode='ltp'
        )
```

## Polling Execution Engine

Located in `sandbox/polling_execution_engine.py`.

### Poll Loop

```python
def _poll_loop(self):
    """Main polling loop - runs every 2 seconds"""
    while self._running:
        try:
            # Get all pending orders
            pending_orders = self._get_pending_orders()

            # Group by symbol for batch price fetch
            symbols = set((o.symbol, o.exchange) for o in pending_orders)

            # Fetch current prices
            prices = self._fetch_prices(symbols)

            # Match orders against prices
            for order in pending_orders:
                ltp = prices.get((order.symbol, order.exchange))
                if ltp:
                    self._try_execute_order(order, ltp)

        except Exception as e:
            logger.error(f"Polling error: {e}")

        time.sleep(2)  # Poll interval
```

## Order Execution Logic

### Price Type Matching

| Price Type | BUY Condition | SELL Condition | Fill Price |
|------------|---------------|----------------|------------|
| MARKET | Execute immediately | Execute immediately | Ask (BUY) / Bid (SELL) |
| LIMIT | LTP <= limit_price | LTP >= limit_price | Limit price |
| SL | LTP >= trigger, LTP <= limit | LTP <= trigger, LTP >= limit | LTP |
| SL-M | LTP >= trigger_price | LTP <= trigger_price | LTP |

### Execution Function

```python
def execute_order(order, execution_price):
    """Execute order at given price"""
    with db_lock:
        # Update order
        order.status = 'COMPLETE'
        order.filled_quantity = order.quantity
        order.average_price = execution_price
        order.exchange_timestamp = datetime.now()

        # Create trade record
        trade = SandboxTrades(
            order_id=order.order_id,
            trade_id=generate_trade_id(),
            symbol=order.symbol,
            exchange=order.exchange,
            action=order.action,
            quantity=order.quantity,
            price=execution_price,
            trade_timestamp=datetime.now()
        )

        # Update position
        position_manager.update_position(
            symbol=order.symbol,
            exchange=order.exchange,
            product=order.product,
            action=order.action,
            quantity=order.quantity,
            price=execution_price
        )

        db.session.add(trade)
        db.session.commit()
```

## Square-Off Manager

Handles automatic position closure at exchange timings.

### Exchange Timings

| Exchange | Product | Square-Off Time |
|----------|---------|-----------------|
| NSE | MIS | 15:15 IST |
| NFO | MIS | 15:15 IST |
| BSE | MIS | 15:15 IST |
| MCX | MIS | 23:30 IST |
| CDS | MIS | 17:00 IST |

### Square-Off Logic

```python
def auto_square_off():
    """Called by scheduler at exchange timings"""
    current_time = datetime.now(IST)

    # Determine which exchanges to square off
    exchanges_to_close = []

    if current_time.hour == 15 and current_time.minute >= 15:
        exchanges_to_close.extend(['NSE', 'NFO', 'BSE'])

    if current_time.hour == 23 and current_time.minute >= 30:
        exchanges_to_close.append('MCX')

    # Close all MIS positions for these exchanges
    for exchange in exchanges_to_close:
        positions = SandboxPositions.query.filter(
            SandboxPositions.exchange == exchange,
            SandboxPositions.product == 'MIS',
            SandboxPositions.quantity != 0
        ).all()

        for position in positions:
            close_position(position)
```

## Settlement Jobs

### T+1 Settlement (Midnight)

```python
@scheduler.scheduled_job('cron', hour=0, minute=1, timezone=IST)
def t1_settlement():
    """Convert CNC positions to holdings"""
    # Get all CNC positions from previous day
    positions = SandboxPositions.query.filter(
        SandboxPositions.product == 'CNC',
        SandboxPositions.quantity != 0
    ).all()

    for position in positions:
        # Create/update holding
        holding = SandboxHoldings.query.filter_by(
            symbol=position.symbol,
            exchange=position.exchange
        ).first()

        if holding:
            # Average down/up existing holding
            new_qty = holding.quantity + position.quantity
            new_avg = (holding.quantity * holding.average_price +
                       position.quantity * position.average_price) / new_qty
            holding.quantity = new_qty
            holding.average_price = new_avg
        else:
            # Create new holding
            holding = SandboxHoldings(
                symbol=position.symbol,
                exchange=position.exchange,
                quantity=position.quantity,
                average_price=position.average_price
            )
            db.session.add(holding)

        # Clear position
        position.quantity = 0
```

### Expired Contract Cleanup

```python
@scheduler.scheduled_job('cron', hour=0, minute=5, timezone=IST)
def cleanup_expired_contracts():
    """Remove expired F&O contracts"""
    today = date.today()

    # Find expired positions
    expired = SandboxPositions.query.filter(
        SandboxPositions.exchange.in_(['NFO', 'MCX', 'CDS']),
        SandboxPositions.quantity != 0
    ).all()

    for position in expired:
        expiry = get_contract_expiry(position.symbol)
        if expiry and today > expiry:
            # Auto-close at last traded price
            close_expired_position(position)
```

## Performance Metrics

| Metric | WebSocket Engine | Polling Engine |
|--------|-----------------|----------------|
| Order matching latency | ~50ms | ~2000ms |
| Price staleness | Real-time | Up to 2 seconds |
| CPU usage | Low (event-driven) | Higher (continuous polling) |
| Network requests | WebSocket subscription | 1 request/symbol/2sec |

## Error Handling

### Connection Loss

```python
def _on_websocket_disconnect(self):
    """Handle WebSocket disconnection"""
    logger.warning("WebSocket disconnected, attempting reconnect...")

    # Retry with backoff
    for attempt in range(5):
        time.sleep(2 ** attempt)
        if self._reconnect():
            logger.info("Reconnected successfully")
            return

    # Fallback to polling
    logger.warning("Falling back to polling engine")
    start_polling_execution_engine()
```

### Database Locks

```python
# Use threading lock for concurrent order updates
_db_lock = threading.Lock()

def execute_order(order, price):
    with _db_lock:
        # All database operations within lock
        ...
```

## Configuration

Environment variables for execution engine:

| Variable | Default | Description |
|----------|---------|-------------|
| `SANDBOX_ENGINE_TYPE` | `websocket` | Engine type: `websocket` or `polling` |
| `SANDBOX_POLL_INTERVAL` | `2` | Polling interval in seconds |
| `SANDBOX_WS_RECONNECT_ATTEMPTS` | `5` | WebSocket reconnection attempts |

## Related Documentation

| Document | Description |
|----------|-------------|
| [Sandbox Architecture](./sandbox-architecture.md) | System architecture |
| [Margin System](./sandbox-margin-system.md) | Margin calculations |
| [WebSocket Proxy](./websocket-proxy.md) | WebSocket server details |



---

# FILE: docs\prd\sandbox-margin-system.md

# Sandbox Margin System

Complete documentation for margin calculation, blocking, and fund management in Sandbox mode.

## Overview

The Sandbox margin system replicates real exchange margin requirements with configurable leverage for sandbox trading.

## Fund Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     Sandbox Account                              │
├─────────────────────────────────────────────────────────────────┤
│  Starting Capital      │  ₹1,00,00,000 (1 Crore)               │
├─────────────────────────────────────────────────────────────────┤
│  Available Balance     │  Capital - Used Margin + Realized P&L │
│  Used Margin           │  Blocked for open positions           │
│  Realized P&L          │  Booked profit/loss from closed trades│
└─────────────────────────────────────────────────────────────────┘
```

## Margin Rules by Product

### Product Types

| Product | Full Form | Leverage | Use Case |
|---------|-----------|----------|----------|
| CNC | Cash and Carry | 1x | Delivery trades (T+1 settlement) |
| MIS | Margin Intraday Square-off | 5x | Intraday trades (auto square-off) |
| NRML | Normal | 1x | F&O overnight positions |

### Margin Calculation

```python
def calculate_margin(symbol, exchange, action, quantity, product, price):
    """Calculate required margin for order"""
    total_value = quantity * price

    if product == 'CNC':
        # Full value required for delivery
        margin = total_value

    elif product == 'MIS':
        # 20% margin (5x leverage) for intraday
        margin = total_value * 0.20

    elif product == 'NRML':
        # Full margin for F&O overnight
        if exchange in ['NFO', 'MCX', 'CDS', 'BFO']:
            margin = total_value
        else:
            margin = total_value

    return margin
```

## Margin Operations

### 1. Block Margin (Order Placement)

```python
def block_margin(amount, description=""):
    """Block margin when placing order"""
    with db_session() as session:
        funds = get_or_create_funds(user_id)

        if funds.available_balance < amount:
            raise InsufficientMarginError(
                f"Required: ₹{amount}, Available: ₹{funds.available_balance}"
            )

        funds.available_balance -= amount
        funds.used_margin += amount

        session.commit()
        return True
```

### 2. Release Margin (Order Cancel/Position Close)

```python
def release_margin(amount, description=""):
    """Release margin when closing position or canceling order"""
    with db_session() as session:
        funds = get_or_create_funds(user_id)

        funds.available_balance += amount
        funds.used_margin -= amount

        # Ensure used_margin doesn't go negative
        if funds.used_margin < 0:
            funds.used_margin = Decimal('0')

        session.commit()
        return True
```

### 3. Book P&L (Position Close)

```python
def book_pnl(pnl_amount, description=""):
    """Book realized P&L when closing position"""
    with db_session() as session:
        funds = get_or_create_funds(user_id)

        # P&L affects both available balance and realized P&L
        funds.available_balance += pnl_amount
        funds.realized_pnl += pnl_amount

        session.commit()
        return True
```

## Order Flow with Margin

### BUY Order Flow

```
┌─────────────────────────────────────────────────────────────┐
│  BUY 100 SBIN @ ₹620 (CNC)                                  │
│  Order Value: ₹62,000                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Calculate Margin                                         │
│     Product: CNC → 100% margin                               │
│     Required: ₹62,000                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Check Available Balance                                  │
│     Available: ₹1,00,00,000                                  │
│     Required: ₹62,000                                        │
│     ✓ Sufficient                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Block Margin                                             │
│     Available: ₹99,38,000 (↓62,000)                         │
│     Used: ₹62,000 (↑62,000)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Create Order (PENDING)                                   │
│     Wait for execution...                                    │
└─────────────────────────────────────────────────────────────┘
```

### SELL Order Flow (Close Long Position)

```
┌─────────────────────────────────────────────────────────────┐
│  Current Position: LONG 100 SBIN @ ₹620                     │
│  Current LTP: ₹625                                           │
│  SELL 100 SBIN @ MARKET                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Execute SELL at ₹625                                     │
│     Trade Value: ₹62,500                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Calculate P&L                                            │
│     Buy Avg: ₹620 × 100 = ₹62,000                           │
│     Sell: ₹625 × 100 = ₹62,500                              │
│     Profit: ₹500                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Release Margin + Book P&L                                │
│     Release margin: ₹62,000                                  │
│     Book profit: ₹500                                        │
│     Available: ₹99,38,000 + ₹62,000 + ₹500 = ₹1,00,00,500   │
│     Used: ₹62,000 - ₹62,000 = ₹0                            │
│     Realized P&L: ₹500                                       │
└─────────────────────────────────────────────────────────────┘
```

## MIS Leverage Example

```
┌─────────────────────────────────────────────────────────────┐
│  BUY 100 SBIN @ ₹620 (MIS - 5x leverage)                    │
│  Order Value: ₹62,000                                        │
│  Margin Required: ₹62,000 × 20% = ₹12,400                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Funds After Order:                                          │
│  Available: ₹1,00,00,000 - ₹12,400 = ₹99,87,600            │
│  Used Margin: ₹12,400                                        │
│                                                              │
│  Buying Power with 5x leverage: ₹99,87,600 × 5 = ₹4.99 Cr  │
└─────────────────────────────────────────────────────────────┘
```

## Holdings Settlement

When CNC positions convert to holdings (T+1):

```python
def transfer_margin_to_holdings(amount, description=""):
    """
    Transfer margin from used_margin to holdings.
    Money is now "locked" in shares, not available for trading.
    """
    with db_session() as session:
        funds = get_or_create_funds(user_id)

        # Release from used_margin (position closed)
        funds.used_margin -= amount

        # Do NOT credit to available_balance
        # Money is now in holdings

        session.commit()
```

### Selling from Holdings

```python
def credit_sale_proceeds(amount, description=""):
    """Credit proceeds from selling holdings back to available balance"""
    with db_session() as session:
        funds = get_or_create_funds(user_id)

        # Sale proceeds go to available balance
        funds.available_balance += amount

        session.commit()
```

## Margin Validation

### Pre-Order Checks

```python
def validate_margin_for_order(order):
    """Comprehensive margin validation before order placement"""

    # 1. Calculate required margin
    margin = calculate_margin(
        order.symbol, order.exchange, order.action,
        order.quantity, order.product, order.price or get_ltp(order.symbol)
    )

    # 2. Check for sell orders
    if order.action == 'SELL':
        if order.product == 'CNC':
            # Check holdings + position
            holdings = get_holdings(order.symbol)
            position = get_position(order.symbol)
            available_qty = (holdings.quantity if holdings else 0) + \
                           (position.quantity if position else 0)

            if order.quantity > available_qty:
                raise InsufficientQuantityError(
                    f"Available: {available_qty}, Requested: {order.quantity}"
                )

            # No margin needed for selling own holdings
            return True

        # For MIS/NRML short selling, margin is needed

    # 3. Check available balance
    funds = get_funds()
    if funds.available_balance < margin:
        raise InsufficientMarginError(
            f"Required: ₹{margin}, Available: ₹{funds.available_balance}"
        )

    return True
```

## API Endpoints

### Get Funds

```
GET /api/v1/funds

Response:
{
    "status": "success",
    "data": {
        "availablecash": 9938000.00,
        "collateral": 0.00,
        "m2mrealized": 500.00,
        "m2munrealized": 250.00,
        "utiliseddebits": 62000.00
    }
}
```

### Reset Funds (Sandbox Only)

```
POST /analyzer/reset-funds

Response:
{
    "status": "success",
    "message": "Funds reset to ₹1,00,00,000"
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `SANDBOX_INITIAL_CAPITAL` | `10000000` | Starting capital (₹1 Cr) |
| `SANDBOX_MIS_LEVERAGE` | `5` | MIS leverage multiplier |
| `SANDBOX_CNC_LEVERAGE` | `1` | CNC leverage (no leverage) |
| `SANDBOX_NRML_LEVERAGE` | `1` | NRML leverage (no leverage) |

## Error Codes

| Code | Message | Resolution |
|------|---------|------------|
| `INSUFFICIENT_MARGIN` | Insufficient margin for order | Reduce quantity or add funds |
| `INSUFFICIENT_HOLDINGS` | Cannot sell more than holdings | Check available quantity |
| `MARGIN_BLOCKED` | Margin already blocked | Wait for previous order |
| `INVALID_PRODUCT` | Unknown product type | Use CNC, MIS, or NRML |

## Related Documentation

| Document | Description |
|----------|-------------|
| [Sandbox Architecture](./sandbox-architecture.md) | System overview |
| [Execution Engine](./sandbox-execution-engine.md) | Order execution |
| [Sandbox PRD](./sandbox.md) | Product requirements |



---

# FILE: docs\prd\sandbox.md

# PRD: Sandbox - Sandbox Trading Environment

> **Status:** ✅ Stable - Fully implemented, production-ready

## Overview

Sandbox (Analyzer Mode) is an isolated sandbox trading environment with simulated capital for testing strategies without risking real money.

## Problem Statement

Traders need to:
- Test new strategies before live deployment
- Validate webhook/API integrations safely
- Learn the platform without financial risk
- Debug issues without affecting real account

## Solution

A complete sandbox trading environment that:
- Uses real-time market prices from broker
- Simulates order execution with realistic fills
- Maintains separate position/order books
- Applies exchange-specific margin rules
- Auto square-off at market close

## Target Users

| User | Use Case |
|------|----------|
| New User | Learn OpenAlgo safely |
| Strategy Developer | Test before live |
| Educator | Demonstrate without risk |
| Debugger | Isolate integration issues |

## Functional Requirements

### FR1: Capital Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Start with configurable capital (default ₹1 Cr) | P0 |
| FR1.2 | Track available/used margin | P0 |
| FR1.3 | Block margin on order placement | P0 |
| FR1.4 | Release margin on position close | P0 |
| FR1.5 | Daily margin reconciliation | P1 |

### FR2: Order Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Place market orders (instant fill at LTP) | P0 |
| FR2.2 | Place limit orders (fill when price reached) | P0 |
| FR2.3 | Place SL/SL-M orders | P1 |
| FR2.4 | Modify pending orders | P1 |
| FR2.5 | Cancel orders | P0 |
| FR2.6 | Order validation (qty, symbol, margin) | P0 |

### FR3: Position Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Track open positions | P0 |
| FR3.2 | Calculate MTM P&L in real-time | P0 |
| FR3.3 | Position netting (same direction, opposite) | P0 |
| FR3.4 | Support MIS/CNC/NRML products | P0 |

### FR4: Holdings (CNC)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | T+1 settlement for delivery trades | P1 |
| FR4.2 | Track buy avg, quantity, P&L | P0 |
| FR4.3 | Sell from holdings | P0 |

### FR5: Auto Square-Off
| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | Square-off MIS at exchange timings | P0 |
| FR5.2 | Exchange-specific timings (NSE 15:15, MCX 23:30) | P0 |
| FR5.3 | Mark expired F&O contracts | P1 |

### FR6: Execution Engine
| ID | Requirement | Priority |
|----|-------------|----------|
| FR6.1 | Poll pending orders every 2 seconds | P0 |
| FR6.2 | Match limit orders against LTP | P0 |
| FR6.3 | Trigger SL orders when price breached | P1 |
| FR6.4 | WebSocket price updates (optional) | P2 |

### FR7: Reporting
| ID | Requirement | Priority |
|----|-------------|----------|
| FR7.1 | Order book with all orders | P0 |
| FR7.2 | Trade book with executions | P0 |
| FR7.3 | Position book with MTM | P0 |
| FR7.4 | P&L summary | P0 |
| FR7.5 | Export to CSV | P2 |

### FR8: Session Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR8.1 | Session boundary at 03:00 IST | P0 |
| FR8.2 | Carry forward NRML/CNC positions | P0 |
| FR8.3 | Reset day's trades at session start | P0 |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Order execution latency | < 500ms |
| Price staleness | < 5 seconds |
| Concurrent orders | 1000+ |
| Database isolation | 100% separate from live |

## Margin Calculation

```
┌──────────────────────────────────────────────────────────┐
│                    Margin Rules                           │
├──────────────────────────────────────────────────────────┤
│ Product │ Leverage │ Margin Required                     │
├─────────┼──────────┼─────────────────────────────────────┤
│ CNC     │ 1x       │ Full value (qty × price)           │
│ MIS     │ 5x       │ 20% of value                       │
│ NRML    │ 1x       │ Full value (F&O overnight)         │
└──────────┴──────────┴─────────────────────────────────────┘
```

## Position Netting Logic

```
Current: +100 shares (LONG)
New Order: SELL 150

Result:
  1. Close existing: SELL 100 (close long)
  2. Open new: SELL 50 (new short position)
  Net: -50 shares (SHORT)
```

## Database Schema

```
sandbox.db (separate from main)
├── sandbox_orders      - All orders
├── sandbox_trades      - Executed trades
├── sandbox_positions   - Open positions
├── sandbox_holdings    - CNC holdings
├── sandbox_funds       - Capital tracking
├── sandbox_margins     - Margin blocks
└── sandbox_logs        - Audit trail
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Request                             │
│                 (Analyzer Mode = ON)                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Order Manager                             │
│  Validate → Check Margin → Create Order → Queue for Exec    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execution Engine                            │
│  Poll Orders → Fetch LTP → Match Price → Execute Trade      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Position Manager                            │
│  Net Position → Update MTM → Block/Release Margin           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Square-Off Manager                          │
│  Check Time → Close MIS → Mark Expired → Settle Holdings    │
└─────────────────────────────────────────────────────────────┘
```

## UI Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ SANDBOX MODE ACTIVE                                      │
│  Capital: ₹1,00,00,000  │  Used: ₹5,00,000  │  P&L: +₹2,500 │
├─────────────────────────────────────────────────────────────┤
│  Open Positions (3)                                          │
│  ┌─────────┬─────┬───────┬─────────┬──────────┬──────────┐ │
│  │ Symbol  │ Qty │ Avg   │ LTP     │ P&L      │ Actions  │ │
│  ├─────────┼─────┼───────┼─────────┼──────────┼──────────┤ │
│  │ SBIN    │ +100│ 620.00│ 625.50  │ +₹550    │ [Close]  │ │
│  │ RELIANCE│ -50 │ 2450  │ 2445.00 │ +₹250    │ [Close]  │ │
│  └─────────┴─────┴───────┴─────────┴──────────┴──────────┘ │
│                                                              │
│  Today's Orders (5)                                          │
│  ┌─────────┬────────┬─────┬────────┬──────────┐            │
│  │ Symbol  │ Action │ Qty │ Status │ Time     │            │
│  ├─────────┼────────┼─────┼────────┼──────────┤            │
│  │ SBIN    │ BUY    │ 100 │ ✓ Done │ 09:15:32 │            │
│  │ INFY    │ BUY    │ 50  │ Pending│ 09:20:15 │            │
│  └─────────┴────────┴─────┴────────┴──────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Related Documentation

| Document | Description |
|----------|-------------|
| [Sandbox Architecture](./sandbox-architecture.md) | Detailed system architecture |
| [Execution Engine](./sandbox-execution-engine.md) | Order matching engine details |
| [Margin System](./sandbox-margin-system.md) | Margin calculation and fund management |

## Key Files Reference

| File | Purpose |
|------|---------|
| `database/sandbox_db.py` | SQLAlchemy models for sandbox tables |
| `blueprints/analyzer.py` | Web routes and API endpoints |
| `services/sandbox_service.py` | Business logic and execution engine |
| `frontend/src/pages/Analyzer.tsx` | React UI component |

## Success Metrics

| Metric | Target |
|--------|--------|
| Price accuracy | Real-time from broker |
| Order fill simulation | Realistic (limit at LTP match) |
| Margin calculation | Match exchange rules |
| Isolation | 0 impact on live account |



---

# FILE: docs\prd\websocket-proxy.md

# PRD: WebSocket Proxy - Real-Time Market Data

> **Status:** ✅ Stable - Fully implemented with connection pooling

## Overview

The WebSocket Proxy is a unified real-time market data streaming system that normalizes data from 29 broker WebSocket APIs into a single interface.

## Problem Statement

Each broker has:
- Different WebSocket protocols and formats
- Different symbol formats and token systems
- Different subscription limits (500-3000 symbols)
- Connection management complexity

Clients need:
- Single WebSocket connection for all data
- Consistent data format regardless of broker
- High-performance streaming for 1000s of symbols

## Solution

A proxy server that:
- Connects to broker-specific WebSocket APIs
- Normalizes data to OpenAlgo format
- Uses ZeroMQ for high-performance internal messaging
- Supports connection pooling for scale

## Target Users

| User | Use Case |
|------|----------|
| React Frontend | Display live prices |
| Python Scripts | Algo trading signals |
| External Apps | Custom dashboards |

## Functional Requirements

### FR1: Client Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | Accept WebSocket connections on port 8765 | P0 |
| FR1.2 | API key authentication | P0 |
| FR1.3 | Track client subscriptions | P0 |
| FR1.4 | Handle client disconnect gracefully | P0 |

### FR2: Subscription Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | Subscribe to symbols (LTP mode) | P0 |
| FR2.2 | Subscribe to symbols (Quote mode) | P0 |
| FR2.3 | Subscribe to symbols (Depth mode) | P1 |
| FR2.4 | Unsubscribe from symbols | P0 |
| FR2.5 | Subscription index for O(1) lookup | P0 |

### FR3: Broker Adapters
| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | Abstract base adapter class | P0 |
| FR3.2 | Zerodha (Kite) adapter | P0 |
| FR3.3 | Angel One adapter | P0 |
| FR3.4 | Dhan adapter | P0 |
| FR3.5 | Other broker adapters (20+) | P1 |
| FR3.6 | Symbol mapping per broker | P0 |

### FR4: Connection Pooling
| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | Multiple connections per broker | P1 |
| FR4.2 | Configurable symbols per connection | P0 |
| FR4.3 | Auto-distribute subscriptions | P1 |
| FR4.4 | Handle connection failures | P0 |

### FR5: Data Normalization
| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | Normalize LTP data | P0 |
| FR5.2 | Normalize OHLC quote data | P0 |
| FR5.3 | Normalize market depth (5 levels) | P1 |
| FR5.4 | Add timestamp if missing | P0 |

### FR6: Performance
| ID | Requirement | Priority |
|----|-------------|----------|
| FR6.1 | Message throttling (50ms minimum) | P0 |
| FR6.2 | Batch message sending | P1 |
| FR6.3 | ZeroMQ pub/sub for internal routing | P0 |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Latency (broker → client) | < 50ms |
| Concurrent clients | 100+ |
| Symbols per user | 3000 |
| Message throughput | 10,000/sec |
| Uptime | 99.9% during market hours |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Clients                                      │
│  React App │ Python SDK │ External Apps                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ WebSocket (ws://localhost:8765)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WebSocket Proxy Server                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   Connection Manager                            │ │
│  │  clients: Dict[client_id, websocket]                           │ │
│  │  subscriptions: Dict[client_id, Set[symbols]]                  │ │
│  │  subscription_index: Dict[(sym,exch,mode), Set[client_ids]]    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               │                                      │
│                               │ ZeroMQ (tcp://127.0.0.1:5555)       │
│                               ▼                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Broker Adapters                              │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │ │
│  │  │ Zerodha  │ │  Angel   │ │   Dhan   │ │  Fyers   │  ...     │ │
│  │  │ 3000 sym │ │ 1000 sym │ │ 1000 sym │ │ 2000 sym │          │ │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │ │
│  │       │            │            │            │                  │ │
│  │       └────────────┴────────────┴────────────┘                  │ │
│  │                         │                                       │ │
│  │                         ▼ Broker WebSocket APIs                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Message Protocol

### Authentication
```json
→ {"action": "authenticate", "api_key": "your_api_key"}
← {"status": "authenticated", "message": "Connected"}
```

### Subscribe
```json
→ {
    "action": "subscribe",
    "symbols": [
      {"symbol": "SBIN", "exchange": "NSE"},
      {"symbol": "RELIANCE", "exchange": "NSE"}
    ],
    "mode": "LTP"
  }
← {"status": "subscribed", "count": 2}
```

### Market Data (LTP)
```json
← {
    "symbol": "SBIN",
    "exchange": "NSE",
    "ltp": 625.50,
    "timestamp": "2024-01-15T10:30:00+05:30"
  }
```

### Market Data (Quote)
```json
← {
    "symbol": "SBIN",
    "exchange": "NSE",
    "ltp": 625.50,
    "open": 620.00,
    "high": 628.00,
    "low": 618.50,
    "close": 622.00,
    "volume": 1500000,
    "timestamp": "2024-01-15T10:30:00+05:30"
  }
```

### Market Data (Depth)
```json
← {
    "symbol": "SBIN",
    "exchange": "NSE",
    "ltp": 625.50,
    "depth": {
      "buy": [
        {"price": 625.45, "quantity": 1000, "orders": 5},
        {"price": 625.40, "quantity": 2500, "orders": 8}
      ],
      "sell": [
        {"price": 625.50, "quantity": 800, "orders": 3},
        {"price": 625.55, "quantity": 1200, "orders": 4}
      ]
    }
  }
```

## ZeroMQ Integration

```
┌─────────────────┐         ┌─────────────────┐
│ Broker Adapter  │         │ Broker Adapter  │
│   (Publisher)   │         │   (Publisher)   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │    ZeroMQ PUB/SUB         │
         │    tcp://127.0.0.1:5555   │
         └───────────┬───────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │    WebSocket Proxy    │
         │     (Subscriber)      │
         │                       │
         │  Receives all ticks   │
         │  Routes to clients    │
         └───────────────────────┘
```

## Configuration

```bash
# Environment Variables
WEBSOCKET_HOST=127.0.0.1
WEBSOCKET_PORT=8765
ZMQ_HOST=127.0.0.1
ZMQ_PORT=5555
MAX_SYMBOLS_PER_WEBSOCKET=1000
MAX_WEBSOCKET_CONNECTIONS=3
```

## Broker Symbol Limits

| Broker | Max Symbols/Connection | Pool Size | Total |
|--------|------------------------|-----------|-------|
| Zerodha | 3000 | 1 | 3000 |
| Angel | 1000 | 3 | 3000 |
| Dhan | 1000 | 3 | 3000 |
| Fyers | 2000 | 2 | 4000 |
| Others | 1000 | 3 | 3000 |

## App Integration

The WebSocket server runs as a daemon thread inside the main Flask app:

```python
# app.py
from websocket_proxy.app_integration import start_websocket_proxy
start_websocket_proxy(app)

# Lifecycle:
# 1. Flask starts
# 2. WebSocket thread spawns (port 8765)
# 3. Both run in same process
# 4. Cleanup on shutdown
```

**Important:** Single Gunicorn worker (`-w 1`) required.

## Key Files

| File | Purpose |
|------|---------|
| `websocket_proxy/server.py` | Main WebSocketProxy class with ZMQ subscription |
| `websocket_proxy/connection_manager.py` | ConnectionPool and SharedZmqPublisher for pooling |
| `websocket_proxy/base_adapter.py` | Abstract broker adapter base class |
| `websocket_proxy/broker_factory.py` | Adapter factory for broker discovery |
| `websocket_proxy/app_integration.py` | Flask startup/shutdown integration |
| `broker/*/streaming/*_adapter.py` | Broker-specific adapter implementations |

## Success Metrics

| Metric | Target |
|--------|--------|
| Message latency | < 50ms |
| Connection stability | 99.9% uptime |
| Symbols supported | 3000 per user |
| Concurrent users | 100+ |

