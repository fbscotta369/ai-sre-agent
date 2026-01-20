```markdown
# 🤖 Local AI-Driven SRE Observability Lab

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white) ![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![ArgoCD](https://img.shields.io/badge/argocd-%23eb5b3e.svg?style=for-the-badge&logo=argo&logoColor=white)

> **A production-grade, air-gapped Kubernetes platform running entirely on local hardware.**

## 📖 Introduction
Welcome! This repository demonstrates how to build a **Self-Healing, AI-Integrated Platform** from scratch. It is designed to simulate a real-world Site Reliability Engineering (SRE) environment.

**What you will build:**
1.  **Infrastructure:** A Kubernetes cluster running locally inside Docker (using **Kind**).
2.  **Automation:** A GitOps pipeline (using **ArgoCD**) that automatically syncs code changes.
3.  **Observability:** A full monitoring stack (**Prometheus & Grafana**) to track metrics.
4.  **Artificial Intelligence:** A local LLM (**Phi-3** via **Ollama**) running inside the cluster.
5.  **The Agent:** A Python-based "AI Detective" that performs automated Root Cause Analysis (RCA).

---

## 🛠️ Prerequisites

| Tool | Purpose | Check Installation |
| :--- | :--- | :--- |
| **Docker** | Runs the virtual nodes | `docker version` |
| **Terraform** | Creates the infrastructure | `terraform -version` |
| **Kubectl** | Talks to the cluster | `kubectl version --client` |
| **Kind** | The local cluster tool | `kind version` |
| **Git** | Manages the code | `git --version` |

*Note: This lab requires a machine with at least **16GB RAM** and **4 CPU Cores**.*

---

## 🚀 Quick Start

### Step 1: Clone & Setup
```bash
git clone [https://github.com/YOUR_USERNAME/sre-lab.git](https://github.com/YOUR_USERNAME/sre-lab.git)
cd sre-lab
chmod +x src/agent.py

```

### Step 2: Infrastructure (Terraform)

```bash
cd terraform
terraform init
terraform apply --auto-approve
# Sanity Check:
kubectl get nodes

```

### Step 3: GitOps Bootstrap

```bash
cd ..
kubectl apply -f k8s/bootstrap.yaml
# Wait 60s for ArgoCD to start

```

### Step 4: Build & Load Images

*We must side-load images because the cluster is local.*

```bash
# Build App
docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab

# Load AI Engine
docker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab

```

### Step 5: Initialize AI Model

```bash
# Wait for Ollama pod to be Running...
kubectl exec -it deployment/ollama -- ollama pull phi3

```

### Step 6: Critical System Tuning

*Required to prevent "Too Many Open Files" errors with Prometheus.*

```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512

```

---

## 🕵️ Run the AI Detective

Launch the internal Kubernetes Job to analyze logs.

```bash
# 1. Upload Script
kubectl create configmap agent-code --from-file=src/agent.py --dry-run=client -o yaml | kubectl apply -f -

# 2. Run Job
kubectl delete job sre-agent-job 2>/dev/null || true
kubectl apply -f k8s/agent-job.yaml

# 3. View Diagnosis
kubectl logs -l job-name=sre-agent-job -f

```

---

## 🧪 Chaos Experiments

Try breaking the app to test the AI.

| Experiment | Action | Expected AI Diagnosis |
| --- | --- | --- |
| **Dev Mode** | Change Dockerfile to `python app.py` | `WARNING: Development server detected` |
| **Memory Leak** | Set `resources.limits.memory` to `10Mi` | `OOMKilled` / `SIGKILL` |

---

## 🧹 Cleanup

```bash
cd terraform
terraform destroy --auto-approve

```

```

---

### 2. `ARCHITECTURE.md` (The "Senior" Brain)
*Added: Mermaid diagram support (GitHub renders this natively now) and cleaner tables.*

```markdown
# 🏗️ Architecture & Design Decisions

> **"The difference between a script and a platform is intention."**
>
> This document details the architectural choices, trade-offs, and production gaps considered during the engineering of this Local SRE Observability Lab.

---

## 📐 High-Level Architecture
The platform follows a **Hub-and-Spoke GitOps Pattern**, adapted for a local air-gapped environment.

```mermaid
graph TD
    subgraph "Host Machine (Local)"
        User[User / Developer] -->|Terraform Apply| Kind[Kind Cluster]
        User -->|Git Push| GitHub[GitHub Repo]
    end

    subgraph "Kubernetes Cluster (Kind)"
        subgraph "Control Plane"
            ArgoCD[ArgoCD Controller]
        end

        subgraph "Data Plane (Worker Nodes)"
            App[Target App (Python)]
            Ollama[AI Engine (Phi-3)]
            Prom[Prometheus]
        end

        subgraph "Ephemeral Operations"
            Agent[AI SRE Agent (Job)]
        end
    end

    GitHub -->|Syncs Manifests| ArgoCD
    ArgoCD -->|Applies State| App & Ollama & Prom
    Prom -->|Scrapes Metrics| App
    Agent -->|Fetches Logs| K8s_API[K8s API Server]
    Agent -->|Sends Text| Ollama
    Ollama -->|Returns Diagnosis| Agent

```

---

## 🧠 Design Decision Records (DDR)

### 1. Infrastructure: Why Kind?

* **The Choice:** `Kind` over `Minikube` or `K3s`.
* **The "Why":** Kind runs nodes as Docker containers. This allows us to simulate a **Multi-Node Cluster** (1 Control Plane, 2 Workers) on a single laptop. This is critical for testing `PodAntiAffinity`, Taints/Tolerations, and node-failure scenarios that single-node setups cannot replicate.

### 2. Delivery: Why Pull-Based GitOps?

* **The Choice:** ArgoCD watching the repo vs. GitHub Actions pushing `kubectl apply`.
* **The "Why":**
* **Security:** The cluster does not expose API credentials. It reaches *out* to fetch changes.
* **Drift Detection:** ArgoCD immediately detects manual edits (`kubectl edit`) and auto-heals the state.



### 3. AI Architecture: Why an Internal Job?

* **The Choice:** Ephemeral `Batch/v1 Job` vs. Host Script.
* **The "Why":**
* **Latency:** Communicates via internal Cluster DNS (10Gbps+), avoiding slow `port-forward` tunnels.
* **Security:** Uses strictly scoped RBAC `ServiceAccount` permissions.



---

## 🚧 Production Gap Analysis

*"If we were deploying this to AWS/GCP tomorrow, what would change?"*

| Component | Lab Implementation | Production Standard | Why Change? |
| --- | --- | --- | --- |
| **Storage** | `HostPath` (Local Disk) | `EBS` / `PersistentDisk` | Local disk dies with the node. Cloud storage replicates data across AZs. |
| **Ingress** | `Port-Forward` | `Ingress Controller` + DNS | Production needs stable DNS (e.g., `app.company.com`) and TLS termination. |
| **Secrets** | Plaintext YAML | External Secrets Operator | Never commit passwords to Git. Inject from Vault/AWS SM at runtime. |
| **AI Engine** | Local CPU Inference | GPU Node Pool | CPU inference blocks the node. Production uses Taints to pin AI to GPUs. |

```
