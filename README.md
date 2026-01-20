# 🤖 Local AI-Driven SRE Observability Platform

![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white) ![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![ArgoCD](https://img.shields.io/badge/argocd-%23eb5b3e.svg?style=for-the-badge&logo=argo&logoColor=white) ![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)

> **A production-grade, air-gapped Kubernetes platform running entirely on local hardware.**

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Prerequisites](#-prerequisites)
3. [Phase 1: Infrastructure Provisioning (Terraform)](#-phase-1-infrastructure-provisioning-terraform)
4. [Phase 2: GitOps Bootstrapping (ArgoCD)](#-phase-2-gitops-bootstrapping-argocd)
5. [Phase 3: The Air-Gap Simulation (Image Injection)](#-phase-3-the-air-gap-simulation-image-injection)
6. [Phase 4: AI Engine Initialization](#-phase-4-ai-engine-initialization)
7. [Phase 5: Critical System Tuning](#-phase-5-critical-system-tuning)
8. [Phase 6: Running the AI SRE Agent](#-phase-6-running-the-ai-sre-agent)
9. [Chaos Engineering Experiments](#-chaos-engineering-experiments)
10. [Accessing Dashboards](#-accessing-dashboards)
11. [Troubleshooting](#-troubleshooting)

---

## 📖 Project Overview
This repository demonstrates a **Self-Healing, AI-Integrated Observability Stack**. It was engineered to solve a critical challenge: **Automating Root Cause Analysis (RCA) in high-security, air-gapped environments.**

Unlike standard "Hello World" tutorials, this lab simulates real-world constraints:
* **No Public Cloud:** Runs on `Kind` (Kubernetes in Docker).
* **No External APIs:** Uses a local LLM (**Phi-3** via **Ollama**) for inference.
* **Strict GitOps:** All infrastructure changes are managed by **ArgoCD**, enforcing state consistency.
* **Kernel-Level Tuning:** Requires modification of host OS `sysctl` parameters to support high-concurrency monitoring workloads.

For a deep dive into the design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🛠 Prerequisites
This lab is resource-intensive. Ensure your machine meets the requirements.

**Hardware Requirements:**
* **RAM:** 16GB minimum (The AI Model + Prometheus stack consumes ~6GB-8GB).
* **CPU:** 4 Cores recommended.
* **Disk:** 20GB free space.

**Software Requirements:**
| Tool | Minimum Version | Check Command |
| :--- | :--- | :--- |
| **Docker** | 24.0+ | `docker version` |
| **Terraform** | 1.5+ | `terraform -version` |
| **Kubectl** | 1.27+ | `kubectl version --client` |
| **Kind** | 0.20+ | `kind version` |
| **Git** | 2.30+ | `git --version` |

---

## 🚀 Phase 1: Infrastructure Provisioning (Terraform)
We use Terraform to ensure the environment is deterministic. This step creates a Docker network and provisions a 3-node Kubernetes cluster (1 Control Plane, 2 Workers).

1.  **Navigate to the Terraform directory:**
    ```bash
    cd terraform
    ```

2.  **Initialize the providers:**
    ```bash
    terraform init
    ```

3.  **Apply the configuration:**
    ```bash
    terraform apply --auto-approve
    ```
    *Time estimate: 2-3 minutes.*

4.  **✅ Verification:**
    Verify the nodes are `Ready`:
    ```bash
    kubectl get nodes
    ```
    *Output should list: `sre-lab-control-plane`, `sre-lab-worker`, `sre-lab-worker2`.*

---

## 🔄 Phase 2: GitOps Bootstrapping (ArgoCD)
We do not manually `kubectl apply` our applications. Instead, we install ArgoCD and tell it to watch this repository.

1.  **Return to the project root:**
    ```bash
    cd ..
    ```

2.  **Deploy the "App of Apps":**
    This manifest installs ArgoCD and configures it to sync the `k8s/manifests/` folder.
    ```bash
    kubectl apply -f k8s/bootstrap.yaml
    ```

3.  **✅ Verification:**
    Watch the ArgoCD pods start up. Wait until all are `Running`.
    ```bash
    kubectl get pods -n argocd -w
    ```

---

## 📦 Phase 3: The Air-Gap Simulation (Image Injection)
Because `Kind` runs inside Docker containers, it cannot see the Docker images on your laptop host. We must "side-load" (inject) the images into the cluster nodes.

1.  **Build the Target Application (v2):**
    This builds our Python Flask app with a production-ready Gunicorn server.
    ```bash
    docker build -t broken-app:v2 src/
    ```

2.  **Inject the App Image:**
    ```bash
    kind load docker-image broken-app:v2 --name sre-lab
    ```

3.  **Pull and Inject the AI Engine:**
    We pull `ollama` to the host first to verify connectivity, then inject it.
    ```bash
    docker pull ollama/ollama:latest
    kind load docker-image ollama/ollama:latest --name sre-lab
    ```

---

## 🧠 Phase 4: AI Engine Initialization
The `ollama` service is now running in the cluster, but it is empty. We need to download the **Phi-3** Large Language Model (LLM) into the cluster's persistent storage.

1.  **Wait for the Ollama Pod:**
    Ensure the `ollama` deployment is ready.
    ```bash
    kubectl rollout status deployment/ollama
    ```

2.  **Download the Model (Inside the Cluster):**
    This command connects to the running pod and triggers the model download (~2.4GB).
    ```bash
    kubectl exec -it deployment/ollama -- ollama pull phi3
    ```

---

## ⚙️ Phase 5: Critical System Tuning
**⚠️ DO NOT SKIP THIS STEP.**

Running Prometheus, Grafana, ArgoCD, and an AI Engine simultaneously opens thousands of file handles. The default Linux limit (8,192) is too low, causing "CrashLoopBackOff" errors.

Run these commands on your **Host Machine**:

```bash
# 1. Increase the maximum number of file watches
sudo sysctl fs.inotify.max_user_watches=524288

# 2. Increase the maximum number of file watch instances
sudo sysctl fs.inotify.max_user_instances=512
🕵️ Phase 6: Running the AI SRE Agent
Now that the platform is stable, we launch the "Detective." This is a Python script running as a Kubernetes Job.

Workflow:

The Job starts and authenticates via a restricted ServiceAccount.

It queries the Kubernetes API for the logs of broken-app.

It sends the logs to http://ollama-svc via the internal cluster network.

It prints the Root Cause Analysis.

Execution:

Bash

# 1. Upload the Agent Script (as a ConfigMap)
kubectl create configmap agent-code --from-file=src/agent.py --dry-run=client -o yaml | kubectl apply -f -

# 2. Launch the Job
# (We delete any previous run first to ensure a clean slate)
kubectl delete job sre-agent-job 2>/dev/null || true
kubectl apply -f k8s/agent-job.yaml

# 3. Watch the Analysis Live
kubectl logs -l job-name=sre-agent-job -f
🧪 Chaos Engineering Experiments
A stable system is boring. Let's break it to prove the AI works.

Scenario A: The "Junior Dev" Mistake (Config Error)
Goal: Trick the AI into detecting a non-production server.

Modify src/Dockerfile: Change the entrypoint to use the Flask development server:

Dockerfile

CMD ["python", "app.py"]
Rebuild and Reload:

Bash

docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab
kubectl rollout restart deployment broken-app
Run the Agent: (See Phase 6).

Result: The AI will warn about "WARNING: Do not use the development server in a production environment."

Scenario B: The Memory Leak (OOM Kill)
Goal: Cause a crash that requires resource analysis.

Modify k8s/manifests/broken-app.yaml: Drastically lower the memory limit to 10MB.

YAML

resources:
  limits:
    memory: "10Mi"
Apply Changes:

Bash

kubectl apply -f k8s/manifests/broken-app.yaml
Run the Agent:

Result: The AI will diagnose an OOMKilled or SIGKILL event.

📊 Accessing Dashboards
Since this is a local cluster, we use port-forward to access the UIs.

ArgoCD UI
Command: kubectl port-forward svc/argocd-server -n argocd 8080:443

URL: https://localhost:8080 (Accept the SSL warning)

Username: admin

Password: Run this to get the password:

Bash

kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
Grafana (Monitoring)
Command: kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80

URL: http://localhost:3000

User: admin

Password: prom-operator

🆘 Troubleshooting
1. failed to create fsnotify watcher: too many open files

Cause: You skipped Phase 5.

Fix: Run the sudo sysctl commands listed in Phase 5.

2. Ollama Connection Error: Read timed out

Cause: Your computer's CPU is overloaded.

Fix: Scale down the monitoring stack to free up resources for the AI:

Bash

kubectl scale deployment -n monitoring --replicas=0 --all
kubectl scale statefulset -n monitoring --replicas=0 --all
3. ImagePullBackOff on broken-app

Cause: You didn't run kind load docker-image. Kind cannot download the image from the internet because it's local.

Fix: Run kind load docker-image broken-app:v2 --name sre-lab.

🧹 Cleanup
To cleanly remove the entire lab and free up your system resources:

Bash

cd terraform
terraform destroy --auto-approve
