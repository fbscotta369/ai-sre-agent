# 🏗️ System Architecture & Design Specification

> **Project:** Local AI-Driven SRE Observability Platform
> **Status:** Production-Ready (Lab Environment)
> **Author:** Baltazar "FB" Scotta
> **Version:** 2.0.0

---

## 📋 Executive Summary

This document outlines the architectural decisions, system components, and data flow of the **AI-Driven SRE Lab**. The platform is designed to emulate a **Self-Healing, Air-Gapped Enterprise Environment** running on local hardware.

The core philosophy is **"GitOps First, AI Augmented."**

1. **Immutable Infrastructure:** No manual changes are allowed in the cluster.
2. **Sovereign AI:** All inference happens locally (Edge AI), ensuring no sensitive log data leaves the network boundary.
3. **Automated Diagnosis:** Operational triage is delegated to an ephemeral internal agent to reduce MTTR (Mean Time to Resolution).
4. **Security by Default:** Containers run as non-root, least-privilege RBAC, pinned dependencies.

---

## 🔭 High-Level Architecture

The system follows a **Hub-and-Spoke GitOps Pattern**, adapted for local execution. It strictly separates the **Control Plane** (ArgoCD), **Data Plane** (Workloads), **Intelligence Plane** (AI Agent), and **Observability Plane** (Monitoring).

```mermaid
graph TD
    subgraph "Host Layer (Local Machine)"
        User[User / SRE]
        Terraform[Terraform CLI]
        Git[GitHub Repository]
        Make[Make / CLI]
    end

    subgraph "Kubernetes Cluster (Kind)"
        direction TB
        
        subgraph "Control Plane Namespace"
            ArgoCD[⚙️ ArgoCD Controller]
        end

        subgraph "Default Namespace (Workloads)"
            App[📦 Target App (Python/Flask)]
            Ollama[🧠 AI Engine (Phi-3)]
            Agent[🕵️ AI SRE Agent (Job)]
        end

        subgraph "Monitoring Namespace"
            Prom[📊 Prometheus]
            Grafana[📈 Grafana]
            NodeExp[📟 Node Exporter]
        end
    end

    %% Flows
    User -->|Define IaC| Terraform
    Terraform -->|Provision| Kind
    User -->|Push Config| Git
    User -->|Dev Commands| Make
    ArgoCD -->|Sync State (Pull)| Git
    ArgoCD -->|Apply Manifests| App & Ollama & Prom
    Prom -->|Scrape Metrics| App
    Prom -->|Scrape Metrics| NodeExp
    Agent -->|Fetch Logs| App
    Agent -->|Request Analysis (HTTP)| Ollama
    Ollama -->|Return Diagnosis| Agent

```

---

## 🕵️ Sequence Design: The AI Agent Workflow

How the "Detective" works internally without external access.

```mermaid
sequenceDiagram
    participant Job as K8s Job (Agent)
    participant API as K8s API Server
    participant App as Target Pod
    participant AI as Ollama Service (Phi-3)

    Note over Job: Job Started by SRE
    Job->>API: Authenticate (ServiceAccount Token)
    API-->>Job: 200 OK (RBAC Check Passed)
    
    Job->>API: GET /api/v1/namespaces/default/pods/broken-app/log
    API->>App: Retrieve stdout/stderr
    App-->>API: Stream Logs
    API-->>Job: Return Raw Logs
    
    Note over Job: Pre-processing (Retry Logic)
    
    loop Retry with Exponential Backoff
        Job->>AI: POST /api/generate (Prompt + Logs)
        Note over AI: Context Loading... Inference...
        AI-->>Job: Return JSON { "response": "Root Cause: OOMKilled..." }
    end
    
    Note over Job: Parse & Print to Stdout
    Job->>Job: Exit Code 0

```

---

## 🧠 Architectural Decision Records (ADR)

*Using the Michael Nygard format (Context, Decision, Consequences).*

### ADR-001: Infrastructure Provisioning Strategy

* **Context:** We need a local Kubernetes environment that closely mimics a cloud-managed service (EKS/GKE) to validate SRE workflows.
* **Decision:** Use **Kind (Kubernetes in Docker)** provisioned via **Terraform**.
* **Discarded Alternatives:**
  * *Minikube:* Good for beginners, but runs as a single VM/Container node by default. Harder to simulate node failures or affinity rules.
  * *K3s:* Lightweight, but API behavior differs slightly from upstream Kubernetes.

* **Consequences:**
  * ✅ Allows multi-node simulation (1 Control, 2 Workers) on a single laptop.
  * ✅ Terraform `kubernetes` provider creates a portable skill set applicable to AWS/Azure.
  * ⚠️ Higher resource overhead (requires Docker running 3 heavy containers).


### ADR-002: GitOps Delivery Model

* **Context:** We need to deploy applications and configurations without manual `kubectl apply` commands to prevent configuration drift.
* **Decision:** **Pull-Based GitOps** using **ArgoCD**.
* **Discarded Alternatives:**
  * *Push-Based (GitHub Actions):* Requires giving GitHub "Admin" credentials to the cluster. Security risk.

* **Consequences:**
  * ✅ **Security:** The cluster requires no inbound access from the internet; it reaches *out* to GitHub.
  * ✅ **Self-Healing:** If a human manually edits a deployment, ArgoCD detects the drift and reverts it immediately.
  * ⚠️ Introduces a "chicken-and-egg" problem: ArgoCD itself must be installed first (bootstrapped manually).


### ADR-003: AI Inference Engine

* **Context:** We need to perform log analysis using an LLM without sending sensitive data to public APIs (OpenAI/Gemini).
* **Decision:** **Ollama** running **Phi-3 Mini (3.8B)** inside the cluster.
* **Discarded Alternatives:**
  * *Llama-3 (8B):* Too heavy for a standard laptop (needs >8GB VRAM).
  * *DeepSeek Coder:* Excellent for code, but Phi-3 is better optimized for reasoning on small hardware.

* **Consequences:**
  * ✅ **Air-Gap:** No data leaves the cluster network.
  * ✅ **Zero Cost:** No API tokens or per-token billing.
  * ⚠️ **Performance:** Inference is CPU-bound and slow (10-15 tokens/sec) compared to cloud GPUs.


### ADR-004: Agent Implementation Language

* **Context:** We need a script to glue the K8s API and the LLM together.
* **Decision:** **Python** (using `requests` with retry logic).
* **Discarded Alternatives:**
  * *Go (Golang):* Standard for K8s tools, but string manipulation and prompt engineering are more verbose than Python.
  * *Bash:* Too fragile for complex JSON parsing and HTTP error handling.

* **Consequences:**
  * ✅ Rapid prototyping and rich ecosystem for text processing.
  * ✅ Built-in retry logic via `urllib3`.
  * ⚠️ Larger container image size (Python runtime vs. Go binary).


### ADR-005: Container Security Posture

* **Context:** We need to run containers securely without root privileges.
* **Decision:** Use non-root user (`appuser`) in Docker images.
* **Discarded Alternatives:**
  * *Running as root:* Simpler but violates principle of least privilege.

* **Consequences:**
  * ✅ **Security:** Containers cannot modify host system files.
  * ✅ **Compliance:** Aligns with CIS Docker Benchmark.
  * ⚠️ Some applications may require file permission adjustments.


---

## 🔒 Security Posture & RBAC

*How we secure the "Internal Detective".*

The AI Agent runs as a **Kubernetes Job**. It does not use the default admin credentials. Instead, we adhere to the **Principle of Least Privilege (PoLP)**.

### ServiceAccount Permissions

The Agent is bound to a specific `Role` that allows ONLY:

1. **VERB:** `get`, `list`
2. **RESOURCE:** `pods`, `pods/log`
3. **NAMESPACE:** `default`

It **cannot** delete pods, read secrets, or modify deployments. This ensures that even if the Agent is compromised (e.g., prompt injection), the attacker cannot destroy the cluster.

### Container Security

- **Non-root user:** All containers run as `appuser` (UID 1000)
- **Read-only root filesystem:** Recommended for production
- **Pinned dependencies:** All Python packages version-pinned
- **No secrets in code:** All credentials via environment variables

---

## 📊 Observability Architecture

The monitoring stack follows the **Prometheus Pull Model**:

```mermaid
graph LR
    subgraph "Targets"
        App[App Pods]
        Node[Node Exporter]
        K8s[Kubernetes API]
    end
    
    subgraph "Scrape Config"
        Config[Prometheus Config]
    end
    
    subgraph "Storage"
        TSDB[(Prometheus TSDB)]
    end
    
    subgraph "Visualization"
        Dash[Grafana Dashboards]
    end
    
    App -->|metrics| Config
    Node -->|metrics| Config
    K8s -->|metrics| Config
    Config -->|scrape| TSDB
    TSDB -->|query| Dash
```

### Metrics Collection

| Target | Endpoint | Scrape Interval |
|--------|----------|----------------|
| broken-app | `prometheus.io/scrape` annotation | 15s |
| Node Exporter | `/metrics` | 15s |
| Kubernetes API | `/apis/*` | 30s |

---

## 🚧 Production Gap Analysis

*Comparing this Lab Environment vs. a Real Enterprise Production Setup.*

| Component | 🏠 Lab Implementation | 🏢 Production Standard | ⚠️ Remediation for Prod |
|-----------|----------------------|------------------------|-------------------------|
| **Storage** | `HostPath` (Local Docker Disk) | `CSI` (EBS / PersistentDisk) | Use cloud storage classes (`gp3`) to ensure data persists across node termination and Availability Zones. |
| **Secrets** | Kubernetes Secrets (YAML) | External Secrets Operator | Integrate with AWS Secrets Manager or HashiCorp Vault. **Never** commit base64 secrets to Git. |
| **Ingress** | `kubectl port-forward` | Ingress Controller + DNS | Deploy Nginx/ALB Ingress Controller with `external-dns` and `cert-manager` for automatic SSL/TLS. |
| **AI Compute** | CPU Inference (Slow) | GPU Node Pool | Use Kubernetes **Taints & Tolerations** to pin AI workloads to GPU-accelerated nodes (e.g., NVIDIA A100/T4). |
| **Scaling** | Manual Replicas | Horizontal Pod Autoscaler | Implement HPA based on Custom Metrics (e.g., Request Rate) using **KEDA**. |
| **Registry** | Sideloaded Images | ECR / GCR / Harbor | Use a private container registry with vulnerability scanning (Trivy/Clair). |
| **Container Security** | Non-root user | Pod Security Standards | Enable **Pod Security Admission** (PSA) with `restricted` policy. |

---

## 📈 Future Roadmap

- **Event-Driven Diagnosis:** Replace the manual Job with a **Prometheus AlertManager Webhook**. When an alert fires (e.g., `KubePodCrashLooping`), it automatically triggers the AI Agent to analyze the specific crashing pod.
- **Vector Database Integration:** Implement **RAG (Retrieval-Augmented Generation)**. Feed the cluster's specific "Runbooks" into a vector DB so the AI can reference company-specific documentation during diagnosis.
- **Multi-Cluster Support:** Extend to federate multiple Kind clusters for distributed training.
- **Metrics-Based Diagnosis:** Expand agent to analyze Prometheus metrics, not just logs.

---

## 📚 Stack & Versions

| Component | Version |
|-----------|---------|
| Kubernetes | v1.27 (Kind) |
| Python | 3.12-slim |
| Flask | 3.0.0 |
| Gunicorn | 21.2.0 |
| Terraform | 1.5+ |
| ArgoCD | v2.10.0 |
| Ollama | latest (Phi-3) |
| Prometheus | v2.45.0 |
| Grafana | v10.0.0 |
| Node Exporter | v1.6.1 |

---

## 🛠 Development Commands

```bash
# Validate environment
make check

# Lint everything
make lint

# Deploy monitoring
kubectl apply -f k8s/manifests/monitoring/

# Run agent manually
kubectl apply -f k8s/agent-job.yaml
kubectl logs -l job-name=sre-agent-job -f
```
