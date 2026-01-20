🤖 Local AI-Driven SRE Observability Platform

A production-grade, air-gapped Kubernetes platform running entirely on local hardware.

📋 Table of Contents

Project Overview

Prerequisites

Phase 1: Infrastructure Provisioning (Terraform)

Phase 2: GitOps Bootstrapping (ArgoCD)

Phase 3: The Air-Gap Simulation (Image Injection)

Phase 4: AI Engine Initialization

Phase 5: Critical System Tuning

Phase 6: Running the AI SRE Agent

Chaos Engineering Experiments

Accessing Dashboards

Troubleshooting

📖 Project Overview

This repository demonstrates a Self-Healing, AI-Integrated Observability Stack. It was engineered to solve a critical challenge: Automating Root Cause Analysis (RCA) in high-security, air-gapped environments.

Unlike standard "Hello World" tutorials, this lab simulates real-world constraints:

No Public Cloud: Runs on Kind (Kubernetes in Docker).

No External APIs: Uses a local LLM (Phi-3 via Ollama) for inference.

Strict GitOps: All infrastructure changes are managed by ArgoCD, enforcing state consistency.

Kernel-Level Tuning: Requires modification of host OS sysctl parameters to support high-concurrency monitoring workloads.

For a deep dive into the design decisions, see ARCHITECTURE.md.

🛠 Prerequisites

This lab is resource-intensive. Ensure your machine meets the requirements.

Hardware Requirements:

RAM: 16GB minimum (The AI Model + Prometheus stack consumes ~6GB-8GB).

CPU: 4 Cores recommended.

Disk: 20GB free space.

Software Requirements:
| Tool | Minimum Version | Check Command |
| :--- | :--- | :--- |
| Docker | 24.0+ | docker version |
| Terraform | 1.5+ | terraform -version |
| Kubectl | 1.27+ | kubectl version --client |
| Kind | 0.20+ | kind version |
| Git | 2.30+ | git --version |

🚀 Phase 1: Infrastructure Provisioning (Terraform)

We use Terraform to ensure the environment is deterministic. This step creates a Docker network and provisions a 3-node Kubernetes cluster (1 Control Plane, 2 Workers).

Navigate to the Terraform directory:

cd terraform


Initialize the providers:

terraform init


Apply the configuration:

terraform apply --auto-approve


Time estimate: 2-3 minutes.

✅ Verification:
Verify the nodes are Ready:

kubectl get nodes


Output should list: sre-lab-control-plane, sre-lab-worker, sre-lab-worker2.

🔄 Phase 2: GitOps Bootstrapping (ArgoCD)

We do not manually kubectl apply our applications. Instead, we install ArgoCD and tell it to watch this repository.

Return to the project root:

cd ..


Deploy the "App of Apps":
This manifest installs ArgoCD and configures it to sync the k8s/manifests/ folder.

kubectl apply -f k8s/bootstrap.yaml


✅ Verification:
Watch the ArgoCD pods start up. Wait until all are Running.

kubectl get pods -n argocd -w


📦 Phase 3: The Air-Gap Simulation (Image Injection)

Because Kind runs inside Docker containers, it cannot see the Docker images on your laptop host. We must "side-load" (inject) the images into the cluster nodes.

Build the Target Application (v2):
This builds our Python Flask app with a production-ready Gunicorn server.

docker build -t broken-app:v2 src/


Inject the App Image:

kind load docker-image broken-app:v2 --name sre-lab


Pull and Inject the AI Engine:
We pull ollama to the host first to verify connectivity, then inject it.

docker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab


🧠 Phase 4: AI Engine Initialization

The ollama service is now running in the cluster, but it is empty. We need to download the Phi-3 Large Language Model (LLM) into the cluster's persistent storage.

Wait for the Ollama Pod:
Ensure the ollama deployment is ready.

kubectl rollout status deployment/ollama


Download the Model (Inside the Cluster):
This command connects to the running pod and triggers the model download (~2.4GB).

kubectl exec -it deployment/ollama -- ollama pull phi3


⚙️ Phase 5: Critical System Tuning

⚠️ DO NOT SKIP THIS STEP.

Running Prometheus, Grafana, ArgoCD, and an AI Engine simultaneously opens thousands of file handles. The default Linux limit (8,192) is too low, causing "CrashLoopBackOff" errors.

Run these commands on your Host Machine:

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

Modify src/Dockerfile:
Change the entrypoint to use the Flask development server:

CMD ["python", "app.py"]


Rebuild and Reload:

docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab
kubectl rollout restart deployment broken-app


Run the Agent: (See Phase 6).

Result: The AI will warn about "WARNING: Do not use the development server in a production environment."

Scenario B: The Memory Leak (OOM Kill)

Goal: Cause a crash that requires resource analysis.

Modify k8s/manifests/broken-app.yaml:
Drastically lower the memory limit to 10MB.

resources:
  limits:
    memory: "10Mi"


Apply Changes:

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

kubectl scale deployment -n monitoring --replicas=0 --all
kubectl scale statefulset -n monitoring --replicas=0 --all


3. ImagePullBackOff on broken-app

Cause: You didn't run kind load docker-image. Kind cannot download the image from the internet because it's local.

Fix: Run kind load docker-image broken-app:v2 --name sre-lab.

🧹 Cleanup

To cleanly remove the entire lab and free up your system resources:

cd terraform
terraform destroy --auto-approve
