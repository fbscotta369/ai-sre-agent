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
Step 2: Infrastructure (Terraform)Bashcd terraform
terraform init
terraform apply --auto-approve
# Sanity Check:
kubectl get nodes
Step 3: GitOps BootstrapBashcd ..
kubectl apply -f k8s/bootstrap.yaml
# Wait 60s for ArgoCD to start
Step 4: Build & Load ImagesWe must side-load images because the cluster is local.Bash# Build App
docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab

# Load AI Engine
docker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab
Step 5: Initialize AI ModelBash# Wait for Ollama pod to be Running...
kubectl exec -it deployment/ollama -- ollama pull phi3
Step 6: Critical System TuningRequired to prevent "Too Many Open Files" errors with Prometheus.Bashsudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
🕵️ Run the AI DetectiveLaunch the internal Kubernetes Job to analyze logs.Bash# 1. Upload Script
kubectl create configmap agent-code --from-file=src/agent.py --dry-run=client -o yaml | kubectl apply -f -

# 2. Run Job
kubectl delete job sre-agent-job 2>/dev/null || true
kubectl apply -f k8s/agent-job.yaml

# 3. View Diagnosis
kubectl logs -l job-name=sre-agent-job -f
🧪 Chaos ExperimentsTry breaking the app to test the AI.ExperimentActionExpected AI DiagnosisDev ModeChange Dockerfile to python app.pyWARNING: Development server detectedMemory LeakSet resources.limits.memory to 10MiOOMKilled / SIGKILL🧹 CleanupBashcd terraform
terraform destroy --auto-approve
