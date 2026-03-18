# 🤖 Local AI-Driven SRE Observability Platform

A production-grade, air-gapped Kubernetes platform running entirely on local hardware.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Phase 1: Infrastructure Provisioning (Terraform)](#phase-1-infrastructure-provisioning-terraform)
- [Phase 2: GitOps Bootstrapping (ArgoCD)](#phase-2-gitops-bootstrapping-argocd)
- [Phase 3: The Air-Gap Simulation (Image Injection)](#phase-3-the-air-gap-simulation-image-injection)
- [Phase 4: AI Engine Initialization](#phase-4-ai-engine-initialization)
- [Phase 5: Critical System Tuning](#phase-5-critical-system-tuning)
- [Phase 6: Running the AI SRE Agent](#phase-6-running-the-ai-sre-agent)
- [Monitoring Stack](#monitoring-stack)
- [Chaos Engineering Experiments](#chaos-engineering-experiments)
- [Accessing Dashboards](#accessing-dashboards)
- [Development Tools](#development-tools)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

---

## 📖 Project Overview

This repository demonstrates a Self-Healing, AI-Integrated Observability Stack. It was engineered to solve a critical challenge: Automating Root Cause Analysis (RCA) in high-security, air-gapped environments.

Unlike standard "Hello World" tutorials, this lab simulates real-world constraints:

- **No Public Cloud:** Runs on Kind (Kubernetes in Docker).
- **No External APIs:** Uses a local LLM (Phi-3 via Ollama) for inference.
- **Strict GitOps:** All infrastructure changes are managed by ArgoCD, enforcing state consistency.
- **Kernel-Level Tuning:** Requires modification of host OS sysctl parameters to support high-concurrency monitoring workloads.
- **Secure by Default:** Runs containers as non-root, uses least-privilege RBAC.

For a deep dive into the design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🛠 Prerequisites

This lab is resource-intensive. Ensure your machine meets the requirements.

### Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 16GB | 32GB |
| CPU | 4 Cores | 8 Cores |
| Disk | 20GB | 50GB |

The AI Model + Prometheus stack consumes ~6GB-8GB.

### Software Requirements

| Tool | Minimum Version | Check Command |
|------|-----------------|---------------|
| Docker | 24.0+ | `docker version` |
| Terraform | 1.5+ | `terraform -version` |
| Kubectl | 1.27+ | `kubectl version --client` |
| Kind | 0.20+ | `kind version` |
| Git | 2.30+ | `git --version` |

### Optional Development Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `make` | Run development tasks | `brew install make` |
| `hadolint` | Lint Dockerfiles | `brew install hadolint` |
| `kubeconform` | Validate K8s manifests | `go install github.com/yannh/kubeconform@latest` |
| `pylint` | Lint Python code | `pip install pylint` |

---

## 📁 Project Structure

```
ai-sre-agent/
├── src/                        # Source code
│   ├── app.py                 # Flask application (demo app)
│   ├── agent.py               # AI SRE Agent (log analysis)
│   ├── Dockerfile            # Container image definition
│   └── .dockerignore         # Docker ignore file
├── k8s/                       # Kubernetes manifests
│   ├── bootstrap.yaml        # ArgoCD bootstrap + App of Apps
│   ├── agent-job.yaml        # SRE Agent Job + RBAC
│   ├── kind-config.yaml      # Kind cluster configuration
│   └── manifests/            # Application manifests
│       ├── broken-app.yaml   # Demo application deployment
│       ├── deployment.yaml   # Service definition
│       ├── ollama.yaml       # Ollama AI engine
│       └── monitoring/       # Observability stack
│           ├── prometheus.yaml
│           ├── grafana.yaml
│           └── node-exporter.yaml
├── terraform/                 # Infrastructure as Code
│   ├── main.tf              # Kind cluster + ArgoCD
│   ├── versions.tf           # Provider versions
│   └── .gitignore
├── scripts/                   # Utility scripts
│   └── check-env.sh          # Environment validation
├── Makefile                   # Development commands
├── README.md                  # Main documentation
├── ARCHITECTURE.md           # System design
├── CONTRIBUTING.md           # Contribution guidelines
└── .env.example              # Environment variables template
```

---

## 🚀 Quick Start

```bash
# 1. Validate environment
make check

# 2. Provision infrastructure
cd terraform && terraform init && terraform apply --auto-approve

# 3. Bootstrap ArgoCD
kubectl apply -f k8s/bootstrap.yaml

# 4. Build and load Docker images
docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab
kind load docker-image ollama/ollama:latest --name sre-lab

# 5. Pull AI model
kubectl exec -it deployment/ollama -- ollama pull phi3

# 6. Run the SRE Agent
kubectl apply -f k8s/agent-job.yaml
kubectl logs -l job-name=sre-agent-job -f
```

---

## Phase 1: Infrastructure Provisioning (Terraform)

We use Terraform to ensure the environment is deterministic. This step creates a Docker network and provisions a 3-node Kubernetes cluster (1 Control Plane, 2 Workers).

```bash
cd terraform
terraform init
terraform apply --auto-approve
```

**Time estimate:** 2-3 minutes.

### Verification

```bash
kubectl get nodes
```

Expected output: `sre-lab-control-plane`, `sre-lab-worker`, `sre-lab-worker2`

---

## Phase 2: GitOps Bootstrapping (ArgoCD)

We do not manually `kubectl apply` our applications. Instead, we install ArgoCD and tell it to watch this repository.

```bash
cd ..
kubectl apply -f k8s/bootstrap.yaml
```

### Verification

```bash
kubectl get pods -n argocd -w
```

Wait until all pods are Running.

### ⚠️ Important: Configure Your Fork

Before ArgoCD can sync, update the repository URL in `k8s/bootstrap.yaml`:

```yaml
data:
  repo.url: https://github.com/YOUR-FORK/ai-sre-agent
```

---

## Phase 3: The Air-Gap Simulation (Image Injection)

Because Kind runs inside Docker containers, it cannot see the Docker images on your laptop host. We must "side-load" (inject) the images into the cluster nodes.

### Build the Target Application

```bash
docker build -t broken-app:v2 src/
```

### Inject the App Image

```bash
kind load docker-image broken-app:v2 --name sre-lab
```

### Pull and Inject the AI Engine

```bash
docker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab
```

---

## Phase 4: AI Engine Initialization

The ollama service is now running in the cluster, but it is empty. We need to download the Phi-3 Large Language Model (LLM) into the cluster's persistent storage.

```bash
kubectl rollout status deployment/ollama
kubectl exec -it deployment/ollama -- ollama pull phi3
```

**Note:** Model download is ~2.4GB and may take several minutes.

---

## Phase 5: Critical System Tuning

⚠️ **DO NOT SKIP THIS STEP.**

Running Prometheus, Grafana, ArgoCD, and an AI Engine simultaneously opens thousands of file handles. The default Linux limit (8,192) is too low, causing "CrashLoopBackOff" errors.

Run these commands on your Host Machine:

```bash
# 1. Increase the maximum number of file watches
sudo sysctl fs.inotify.max_user_watches=524288

# 2. Increase the maximum number of file watch instances
sudo sysctl fs.inotify.max_user_instances=512
```

To make these changes persistent across reboots, add to `/etc/sysctl.conf`:

```bash
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
echo "fs.inotify.max_user_instances=512" | sudo tee -a /etc/sysctl.conf
```

---

## Phase 6: Running the AI SRE Agent

Now that the platform is stable, we launch the "Detective." This is a Python script running as a Kubernetes Job.

### Workflow

1. The Job starts and authenticates via a restricted ServiceAccount
2. It queries the Kubernetes API for the logs of broken-app
3. It sends the logs to Ollama via the internal cluster network
4. It prints the Root Cause Analysis

### Execution

```bash
# 1. Upload the Agent Script (as a ConfigMap)
kubectl create configmap agent-code --from-file=src/agent.py --dry-run=client -o yaml | kubectl apply -f -

# 2. Launch the Job
kubectl delete job sre-agent-job 2>/dev/null || true
kubectl apply -f k8s/agent-job.yaml

# 3. Watch the Analysis Live
kubectl logs -l job-name=sre-agent-job -f
```

### Agent Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | Provider: `ollama` or `google` |
| `OLLAMA_HOST` | `ollama-svc` | Ollama service name |
| `OLLAMA_NAMESPACE` | `default` | Ollama namespace |
| `OLLAMA_MODEL` | `phi3` | Model to use |
| `OLLAMA_TIMEOUT` | `60` | Request timeout (seconds) |
| `OLLAMA_MAX_RETRIES` | `3` | Number of retries |
| `POD_NAME` | `broken-app` | Target pod label |

---

## 📊 Monitoring Stack

The platform includes a complete observability stack:

### Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Prometheus** | Metrics collection | 9090 |
| **Grafana** | Dashboards & visualization | 3000 |
| **Node Exporter** | Node-level metrics | 9100 |

### Deploy Monitoring

```bash
kubectl apply -f k8s/manifests/monitoring/
```

### Prometheus Targets

The monitoring stack automatically scrapes:

- Kubernetes API servers
- Kubernetes nodes
- Pods with `prometheus.io/scrape=true` annotation
- Node Exporter for system metrics

---

## 🧪 Chaos Engineering Experiments

A stable system is boring. Let's break it to prove the AI works.

### Scenario A: The "Junior Dev" Mistake (Config Error)

Goal: Trick the AI into detecting a non-production server.

1. Modify `src/Dockerfile`:
   ```dockerfile
   CMD ["python", "app.py"]
   ```

2. Rebuild and Reload:
   ```bash
   docker build -t broken-app:v2 src/
   kind load docker-image broken-app:v2 --name sre-lab
   kubectl rollout restart deployment broken-app
   ```

3. Run the Agent (See Phase 6).

**Result:** The AI will warn about "WARNING: Do not use the development server in a production environment."

### Scenario B: The Memory Leak (OOM Kill)

Goal: Cause a crash that requires resource analysis.

1. Modify `k8s/manifests/broken-app.yaml`:
   ```yaml
   resources:
     limits:
       memory: "10Mi"
   ```

2. Apply Changes:
   ```bash
   kubectl apply -f k8s/manifests/broken-app.yaml
   ```

3. Run the Agent.

**Result:** The AI will diagnose an OOMKilled or SIGKILL event.

---

## 📊 Accessing Dashboards

Since this is a local cluster, we use port-forward to access the UIs.

### ArgoCD UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

- **URL:** https://localhost:8080 (Accept the SSL warning)
- **Username:** admin
- **Password:** `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

### Grafana (Monitoring)

```bash
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
```

- **URL:** http://localhost:3000
- **Username:** admin
- **Password:** prom-operator

### Prometheus

```bash
kubectl port-forward svc/prometheus -n monitoring 9090:9090
```

- **URL:** http://localhost:9090

---

## 🛠 Development Tools

This project includes a Makefile with useful development commands.

### Available Commands

```bash
make help              # Show available targets
make check             # Run environment check
make lint              # Run all linters
make lint-docker       # Lint Dockerfiles
make lint-k8s          # Validate K8s manifests
make lint-python       # Lint Python code
make validate          # Validate YAML syntax
make test              # Run tests
make clean             # Clean up generated files
make install-deps      # Install development dependencies
make terraform-validate # Validate Terraform
```

---

## 🆘 Troubleshooting

### 1. failed to create fsnotify watcher: too many open files

**Cause:** You skipped Phase 5.

**Fix:** Run the sudo sysctl commands listed in Phase 5.

### 2. Ollama Connection Error: Read timed out

**Cause:** Your computer's CPU is overloaded.

**Fix:** Scale down the monitoring stack to free up resources for the AI:

```bash
kubectl scale deployment -n monitoring --replicas=0 --all
kubectl scale statefulset -n monitoring --replicas=0 --all
```

### 3. ImagePullBackOff on broken-app

**Cause:** You didn't run `kind load docker-image`. Kind cannot download the image from the internet because it's local.

**Fix:** Run `kind load docker-image broken-app:v2 --name sre-lab`.

### 4. Agent Job fails with "Error: kubectl not found in PATH"

**Cause:** The agent container doesn't have kubectl installed.

**Fix:** The agent runs inside the cluster and uses the in-cluster configuration. Ensure the ServiceAccount has proper RBAC permissions.

### 5. Prometheus not scraping metrics

**Cause:** Pod missing scrape annotations.

**Fix:** Ensure your pod has:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "5000"
```

---

## 🧹 Cleanup

To cleanly remove the entire lab and free up your system resources:

```bash
cd terraform
terraform destroy --auto-approve
```

---

## 📚 Stack & Versions

| Component | Version |
|-----------|---------|
| Kubernetes | v1.27 (Kind) |
| Python | 3.12-slim |
| Terraform | 1.5+ |
| ArgoCD | v2.10.0 |
| Ollama | latest (Phi-3) |
| Prometheus | v2.45.0 |
| Grafana | v10.0.0 |
| Node Exporter | v1.6.1 |

---

## 🔒 Security Features

- **Non-root containers:** Applications run as non-root user (`appuser`)
- **Least-privilege RBAC:** Agent has read-only access to pods/logs only
- **Pinned dependencies:** All Python packages are version-pinned
- **No secrets in code:** All secrets via environment variables
- **GitOps enforcement:** All changes through ArgoCD
