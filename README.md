# 🤖 Local AI-Driven SRE Observability Lab

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white) ![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![ArgoCD](https://img.shields.io/badge/argocd-%23eb5b3e.svg?style=for-the-badge&logo=argo&logoColor=white) ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white) ![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)

> **A production-grade, air-gapped Kubernetes platform running entirely on local hardware.**

## 📋 Table of Contents
1. [Introduction](#-introduction)
2. [Architecture Overview](#-architecture-overview)
3. [Prerequisites](#-prerequisites)
4. [Installation & Setup](#-installation--setup)
5. [The AI Detective (How to Run)](#-the-ai-detective-how-to-run)
6. [Chaos Engineering (Break It!)](#-chaos-engineering-experiments)
7. [Troubleshooting](#-troubleshooting)

---

## 📖 Introduction
Welcome to the **SRE AI Lab**. This project was engineered to solve a specific problem: **How do we build a self-healing, AI-integrated observability stack without relying on public cloud APIs?**

This repository is not just a script; it is a full-platform simulation that demonstrates:
* **Infrastructure as Code (IaC):** Provisioning a multi-node cluster using Terraform.
* **GitOps Principles:** Using ArgoCD to enforce state and prevent configuration drift.
* **Edge AI:** Running Large Language Models (LLMs) *inside* the cluster for air-gapped log analysis.
* **Advanced Observability:** Tuning Linux Kernel limits to support heavy Prometheus workloads.

---

## 🏗 Architecture Overview
This lab uses a **Hub-and-Spoke GitOps pattern**.

* **The Infrastructure:** `Kind` (Kubernetes in Docker) simulates a 3-node cluster (1 Control Plane, 2 Workers) on your local machine.
* **The "Brain" (GitOps):** `ArgoCD` watches this GitHub repository. When you commit changes to the `k8s/` folder, ArgoCD automatically syncs them to the cluster.
* **The Intelligence:** An internal **AI SRE Agent** (Python) runs as a Kubernetes Job. It queries the Kubernetes API for logs, sends them to a local LLM service (**Ollama** running Phi-3), and returns a Root Cause Analysis (RCA).

For a deep dive into the design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🛠 Prerequisites
Ensure your environment is ready before starting. This lab is resource-intensive.

* **OS:** Linux, macOS, or Windows (WSL2).
* **Hardware:** Minimum **16GB RAM** (AI models need ~4GB just to load) and **4 CPU Cores**.

| Tool | Minimum Version | Check Command |
| :--- | :--- | :--- |
| **Docker** | 24.0+ | `docker version` |
| **Terraform** | 1.5+ | `terraform -version` |
| **Kubectl** | 1.27+ | `kubectl version --client` |
| **Kind** | 0.20+ | `kind version` |

---

## 🚀 Installation & Setup

### Phase 1: Provision Infrastructure (Terraform)
We use Terraform to guarantee a reproducible environment. This creates the Docker network and the Kind cluster nodes.

```bash
cd terraform
# Initialize Terraform providers
terraform init

## Apply the configuration (Type 'yes' if prompted, or use auto-approve)
terraform apply --auto-approve
✅ Verification: Run kubectl get nodes. You should see three nodes:

sre-lab-control-plane (Ready)

sre-lab-worker (Ready)

sre-lab-worker2 (Ready)

Phase 2: Bootstrap GitOps (ArgoCD)
We install ArgoCD to handle all future deployments.

Bash

cd ..
# Apply the "App of Apps" pattern
kubectl apply -f k8s/bootstrap.yaml
✅ Verification: Wait ~2 minutes, then run kubectl get pods -n argocd. Ensure all pods are Running.

Phase 3: The "Air-Gap" Simulation (Image Loading)
Because this cluster runs locally, it cannot pull custom images from your laptop's filesystem. We must "side-load" them directly into the cluster nodes.

1. Build the Target App (v2):

Bash

docker build -t broken-app:v2 src/
2. Inject Images into Kind:

Bash

# Load our custom app
kind load docker-image broken-app:v2 --name sre-lab

# Load the AI Engine (Ollama)
# We pull it to the host first to avoid massive downloads inside the cluster
docker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab
Phase 4: Initialize the AI Model
The ollama service is now running, but it has no "Brain" yet. We need to download the Phi-3 model into its persistent volume.

Bash

# Execute the pull command INSIDE the running pod
kubectl exec -it deployment/ollama -- ollama pull phi3
(Note: This download is ~2.4GB. It only happens once.)

Phase 5: Production Tuning (CRITICAL)
This is a standard SRE task. Default Linux settings limit how many files a user can "watch". Prometheus and Grafana open thousands of file handles. If we don't fix this, the cluster will crash with too many open files.

Bash

# Apply sysctl fixes on your HOST machine
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
🕵️ The AI Detective (How to Run)
Now that the platform is stable, let's run the AI SRE Agent. This is a Python script wrapped in a Kubernetes Job. It:

Connects to the K8s API (ServiceAccount).

Fetches logs from the broken-app.

Sends logs to the internal ollama service.

Prints a diagnosis.

Bash

# 1. Upload the Agent Code as a ConfigMap
kubectl create configmap agent-code --from-file=src/agent.py --dry-run=client -o yaml | kubectl apply -f -

# 2. Launch the Detective Job
kubectl delete job sre-agent-job 2>/dev/null || true
kubectl apply -f k8s/agent-job.yaml

# 3. Watch the analysis live
kubectl logs -l job-name=sre-agent-job -f
🧪 Chaos Engineering Experiments
A stable system is boring. Let's break it to test the AI's capabilities.

Scenario A: The "Junior Dev" Mistake
The Break: Change the application to run with a Flask Development Server instead of Gunicorn.

Edit src/Dockerfile: Change CMD to ["python", "app.py"].

Rebuild & Reload:

Bash

docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab
kubectl rollout restart deployment broken-app
Run the Agent.

Expected Result: The AI should warn: "WARNING: Do not use the development server in a production environment."

Scenario B: The Memory Leak (OOM Kill)
The Break: Starve the application of RAM.

Edit k8s/manifests/broken-app.yaml.

Change resources.limits.memory to 10Mi.

Apply the change: kubectl apply -f k8s/manifests/broken-app.yaml

Run the Agent.

Expected Result: The AI should diagnose: "Container is crashing due to Out Of Memory (OOMKilled) or SIGKILL signals."

🆘 Troubleshooting
Q: The AI Agent says "Read timed out"

Reason: Your CPU is overloaded. Running K8s + Prometheus + AI on one laptop is heavy.

Fix: Scale down monitoring to free up resources for the AI:

Bash

kubectl scale deployment -n monitoring --replicas=0 --all
Q: failed to create fsnotify watcher

Reason: You skipped Phase 5: Production Tuning.

Fix: Re-run the sudo sysctl commands.

🧹 Cleanup
To free up your computer's resources:

Bash

cd terraform
terraform destroy --auto-approve
