# 🤖 AI-Driven SRE Platform (Hybrid Architecture)

A production-grade Kubernetes platform featuring **Autonomous AI Agents**, **GitOps Automation**, and **Hybrid Inference** (Public/Private LLMs).

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![ArgoCD](https://img.shields.io/badge/argocd-%23eb5b46.svg?style=for-the-badge&logo=argo&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_AI-333333?style=for-the-badge)

## 📖 Architecture & Design Decisions (ADR)

This section documents the technical reasoning behind the architecture, addressing Security, Cost, and Resilience.

### 1. Why Hybrid AI (Google Gemini + Local Ollama)?
**The Challenge:** Balancing advanced reasoning capabilities with strict data privacy and cost control.
* **Decision:** Implemented a **Hybrid Provider Pattern**.
    * **Public (Google Gemini):** Used for complex Root Cause Analysis (RCA) where "Senior-level" reasoning is required.
    * **Private (Ollama/Gemma):** Used for PII scrubbing and high-compliance environments.
* **Why not just Cloud?** Security. In Fintech/Healthcare, sending raw logs to a public API is a violation. Local LLMs ensure **Data Sovereignty** (data never leaves the VPC).
* **Why not just Local?** Performance. Running massive reasoning models on local CPUs introduces latency. The hybrid approach optimizes for the specific task.

### 2. Why Pull-Based GitOps (ArgoCD) vs. Push (GitHub Actions)?
**The Challenge:** Securely synchronizing cluster state without exposing credentials.
* **Decision:** **Pull Model**. ArgoCD sits inside the cluster and watches the repo.
* **Security:** In a Push model (CI/CD), Admin keys must be stored in GitHub Secrets. If GitHub is compromised, the cluster is lost. In the Pull model, credentials never leave the cluster.
* **Drift Detection:** ArgoCD provides continuous monitoring. If someone manually changes a replica count (Drift), ArgoCD detects and reverts it instantly. CI/CD pipelines only run on commit, missing manual drift.

### 3. Resilience: What if GitHub goes down?
**The Challenge:** Ensuring production stability during dependency outages.
* **Analysis:** ArgoCD relies on GitHub availability to sync.
* **Failure Mode:** If GitHub fails, ArgoCD cannot fetch updates, but **existing pods continue running**. The production environment remains stable (fails open).
* **Emergency Protocol:** In a "Break Glass" scenario during a GitHub outage, we pause ArgoCD and apply hotfixes directly via `kubectl`. Once GitHub returns, we commit the changes to restore the GitOps loop.

---

## 🚀 Quick Start: From Zero to Hero

Follow these steps to clone this repo and run the full stack on a local machine.

### Prerequisites
* Docker Desktop / Daemon
* [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
* [Kubectl](https://kubernetes.io/docs/tasks/tools/)
* Python 3.9+

### Step 1: Initialize Infrastructure
Create the cluster and deploy the core stack.

```bash
# 1. Clone the repository
git clone https://github.com/fbscotta369/ai-sre-agent.git
cd ai-sre-agent

# 2. Create the Kubernetes Cluster (Kind)
kind create cluster --config k8s/kind-config.yaml --name sre-lab

# 3. Deploy the Application Stack (Broken App + Ollama)
kubectl apply -f k8s/manifests/
```

### Step 2: Configure GitOps (ArgoCD)
Install ArgoCD to manage the cluster state automatically.

```bash
# 1. Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Access the Dashboard (Port Forward)
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Login at https://localhost:8080 (User: admin)
# Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

### Step 3: Initialize Sovereign AI (Local LLM)
Download the brain for the local AI provider.

```bash
# 1. Wait for Ollama pod to be Ready
kubectl wait --for=condition=ready pod -l app=ollama --timeout=300s

# 2. Pull the Gemma:2b Model (Google's Open Model)
kubectl exec -it deployment/ollama -- ollama pull gemma:2b

# 3. Open Tunnel for the Agent
kubectl port-forward svc/ollama-svc 11434:80
```

### Step 4: Run the AI Agent
You can run the agent in two modes.

**Mode A: Sovereign Mode (Local/Private)**
```bash
# In a new terminal
export LLM_PROVIDER="ollama"
export OLLAMA_URL="http://localhost:11434/api/generate"
python3 src/agent.py
```

**Mode B: Cloud Mode (Google Gemini)**
```bash
export LLM_PROVIDER="google"
export GEMINI_API_KEY="your-api-key-here"
python3 src/agent.py
```

---

## 🛠 Tech Stack
* **Infrastructure:** Kind, Docker, Kubernetes
* **Automation:** ArgoCD (GitOps)
* **AI/ML:** Google Gemini 2.0 Flash, Ollama, Gemma:2b
* **Languages:** Python (Flask, Requests)
