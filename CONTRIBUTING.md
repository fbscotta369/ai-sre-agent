# Contributing to AI SRE Agent

Thank you for your interest in contributing to the AI SRE Agent project!

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guide](#code-style-guide)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Decision Records](#decision-records)
- [Testing Guidelines](#testing-guidelines)
- [Security Guidelines](#security-guidelines)
- [Reporting Issues](#reporting-issues)
- [License](#license)

---

## Getting Started

### Fork and Clone

1. **Fork** the repository on GitHub
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR-FORK/ai-sre-agent.git
   cd ai-sre-agent
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/anomalyco/ai-sre-agent.git
   ```

### Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

---

## Development Workflow

### Prerequisites

Ensure you have the following installed:

- Docker 24.0+
- Terraform 1.5+
- kubectl 1.27+
- Kind 0.20+
- Python 3.12+
- Make

### Setting Up Development Environment

```bash
# Install development dependencies
make install-deps

# Validate your environment
make check

# Run linters
make lint
```

### Making Changes

1. **Code Style:** Follow the guidelines in this document
2. **Testing:** Add tests for new functionality
3. **Documentation:** Update README.md and ARCHITECTURE.md as needed
4. **Validation:** Run `make lint` before committing

### Validating Your Changes

```bash
# Lint all code
make lint

# Validate Kubernetes manifests
make lint-k8s

# Validate Python code
make lint-python

# Validate YAML syntax
make validate

# Validate Terraform
make terraform-validate
```

---

## Code Style Guide

### Python

We follow PEP 8 with some modifications:

- **Maximum line length:** 100 characters
- **Type hints:** Use where possible
- **Docstrings:** Use Google style

```python
def fetch_logs(pod_label: str, tail: int = 50) -> str:
    """Fetch logs from pods matching the given label.

    Args:
        pod_label: Label selector for pods.
        tail: Number of lines to fetch from the end.

    Returns:
        Log output as string, or error message.

    Raises:
        subprocess.TimeoutExpired: If kubectl times out.
    """
    pass
```

**Why 100 characters?**
> 80 is too restrictive for modern displays. 100 is a good balance between readability and not wrapping code too often.

### Kubernetes YAML

- **Indentation:** 2 spaces (standard)
- **Labels:** Include for all resources
- **Annotations:** Use for Prometheus scrape configs
- **Resource limits:** Always specify for containers
- **Probes:** Use for long-running containers

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      containers:
      - name: app
        image: my-app:v1
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
```

**Why always set resource limits?**
> Without limits, pods can consume unlimited resources and cause node-level issues. Always set both requests (guaranteed) and limits (maximum).

### Terraform

- **Provider pinning:** Always pin provider versions
- **Resource naming:** Use descriptive names
- **Outputs:** Document all outputs

---

## Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes nor adds |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

### Examples

```bash
# Good commit messages
git commit -m "feat(agent): add retry logic with exponential backoff"
git commit -m "fix(dockerfile): use non-root user for security"
git commit -m "docs(readme): add troubleshooting section"
git commit -m "refactor(monitoring): separate Prometheus config"

# Bad commit messages
git commit -m "fixed stuff"
git commit -m "WIP"
git commit -m "update"
```

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks:**
   ```bash
   make lint
   make validate
   ```

3. **Test locally** if applicable

### PR Description Template

```markdown
## Summary
Brief description of the change.

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Screenshots (if applicable)
```

### Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Once approved, maintainers will merge

---

## Decision Records

When making significant architectural changes, please document them using ADRs (Architecture Decision Records).

### ADR Template

```markdown
### ADR-XXX: Title

* **Context:** Situation requiring a decision
* **Decision:** What we decided
* **Alternatives Considered:**
  - Option A: Description
  - Option B: Description
* **Consequences:**
  - Positive: Benefit 1, Benefit 2
  - Negative: Drawback 1, Drawback 2
```

### When to Create an ADR?

Create an ADR when you:

- Add a new component
- Change a technology choice
- Modify the architecture
- Change security model

---

## Testing Guidelines

### Unit Tests

For Python code, use pytest:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest src/tests/

# Run with coverage
pytest --cov=src tests/
```

### Integration Tests

For Kubernetes manifests:

```bash
# Validate all YAML
make validate

# Check resources exist
kubectl apply --dry-run=client -f k8s/manifests/
```

---

## Security Guidelines

### Never Commit Secrets

- **Do not** commit `.env` files
- **Do not** commit API keys
- **Do not** commit passwords
- Use environment variables or Kubernetes secrets

### Container Security

- **Non-root user:** Always run as non-root
- **Read-only root filesystem:** When possible
- **Pinned dependencies:** Always pin versions in Dockerfiles

```dockerfile
# Good
RUN pip install flask==3.0.0

# Bad
RUN pip install flask  # No version!
```

### RBAC

- Use least privilege for ServiceAccounts
- Avoid cluster-admin when possible
- Document all permissions

---

## Reporting Issues

When reporting issues, please include:

1. **Description:** What is the problem?
2. **Steps to Reproduce:** How to trigger it
3. **Expected vs Actual:** What should happen vs what happens
4. **Environment:**
   - OS and version
   - Docker version
   - Kubernetes version
   - Kind version
5. **Log Output:** Relevant logs and error messages
6. **Screenshots:** If applicable

### Issue Template

```markdown
## Bug Description


## Steps to Reproduce
1.
2.
3.

## Expected Behavior


## Actual Behavior


## Environment
- OS:
- Docker:
- Kubernetes:
- Kind:

## Logs

```

---

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

## Quick Reference

```bash
# Install dependencies
make install-deps

# Validate everything
make lint
make validate

# Run environment check
make check

# Create a feature branch
git checkout -b feature/my-feature

# Commit changes
git add .
git commit -m "feat(scope): description"

# Push to fork
git push origin feature/my-feature

# Create PR on GitHub
```
