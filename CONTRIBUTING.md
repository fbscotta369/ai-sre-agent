# Contributing to AI SRE Agent

Thank you for your interest in contributing to the AI SRE Agent project!

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR-FORK/ai-sre-agent.git`
3. **Create** a feature branch: `git checkout -b feature/your-feature-name`

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

1. **Code Style**: Follow PEP 8 for Python, K8s YAML best practices
2. **Testing**: Add tests for new functionality
3. **Documentation**: Update README.md and ARCHITECTURE.md as needed

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
```

### Submitting Changes

1. **Commit** your changes with a clear commit message
2. **Push** to your fork
3. **Create a Pull Request** against the main repository

## Project Structure

```
ai-sre-agent/
├── src/                    # Source code
│   ├── app.py             # Flask application
│   ├── agent.py           # AI SRE Agent
│   └── Dockerfile         # Container image
├── k8s/                   # Kubernetes manifests
│   ├── manifests/         # Application manifests
│   │   ├── broken-app.yaml
│   │   ├── deployment.yaml
│   │   ├── ollama.yaml
│   │   └── monitoring/    # Prometheus, Grafana
│   ├── bootstrap.yaml     # ArgoCD bootstrap
│   └── agent-job.yaml     # Agent job definition
├── terraform/             # Infrastructure code
├── scripts/               # Utility scripts
├── Makefile              # Development commands
└── README.md             # Project documentation
```

## Coding Standards

### Python

- Use type hints where possible
- Follow PEP 8 style guide
- Maximum line length: 100 characters
- Use meaningful variable names

### Kubernetes YAML

- Use consistent indentation (2 spaces)
- Include labels for all resources
- Specify resource limits for containers
- Use probes (liveness/readiness) for long-running containers

### Git Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Fix bug" not "Fixes bug")
- Reference issues and pull requests

## Security Guidelines

- **Never commit secrets** - Use environment variables or Kubernetes secrets
- **Run as non-root** - All containers should run as non-root user
- **Least privilege** - Use minimal RBAC permissions
- **Pin dependencies** - Always pin package versions in Dockerfiles

## Reporting Issues

When reporting issues, please include:

1. **Description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Docker version, Kubernetes version)
5. **Log output** if applicable

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
