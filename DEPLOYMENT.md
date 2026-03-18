# Deployment Guide

This guide provides detailed, step-by-step instructions for deploying the AI SRE Agent platform.

## Table of Contents

- [Prerequisites Check](#prerequisites-check)
- [Phase 1: Infrastructure](#phase-1-infrastructure)
- [Phase 2: GitOps Setup](#phase-2-gitops-setup)
- [Phase 3: Container Images](#phase-3-container-images)
- [Phase 4: AI Engine](#phase-4-ai-engine)
- [Phase 5: System Tuning](#phase-5-system-tuning)
- [Phase 6: Deploy Applications](#phase-6-deploy-applications)
- [Phase 7: Run Agent](#phase-7-run-agent)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites Check

Before starting, verify your environment:

```bash
# Check all prerequisites
make check
```

Expected output:
```
✓ docker is installed
✓ terraform is installed
✓ kubectl is installed
✓ kind is installed
✓ git is installed
✓ Docker is running
✓ Kind cluster 'sre-lab' exists
✓ Node sre-lab-control-plane is Ready
✓ Node sre-lab-worker is Ready
✓ Node sre-lab-worker2 is Ready
```

If any checks fail, install the missing tool before proceeding.

---

## Phase 1: Infrastructure

### Step 1.1: Navigate to Terraform Directory

```bash
cd terraform
```

### Step 1.2: Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing provider plugins...
- Finding hashicorp/kind versions matching "0.2.0"...
- Finding hashicorp/helm versions matching "2.12.1"...
...
Terraform has been successfully initialized!
```

### Step 1.3: Review the Plan (Optional but Recommended)

```bash
terraform plan
```

This shows what resources will be created:
- 1 Kind cluster (3 nodes)
- 1 Helm release (ArgoCD)

### Step 1.4: Apply the Configuration

```bash
terraform apply --auto-approve
```

**Time estimate:** 2-5 minutes depending on your internet speed.

Expected output:
```
Apply complete! Resources:
  kind_cluster.sre_lab will be created
  helm_release.argocd will be created
```

### Step 1.5: Verify Cluster

```bash
kubectl get nodes
```

Expected output:
```
NAME                      STATUS   ROLES           AGE   VERSION
sre-lab-control-plane     Ready    control-plane   2m    v1.27.3
sre-lab-worker            Ready    <none>          1m    v1.27.3
sre-lab-worker2           Ready    <none>          1m    v1m    v1.27.3
```

### Step 1.6: Verify ArgoCD Installation

```bash
kubectl get pods -n argocd
```

Expected output:
```
NAME                                  READY   STATUS    RESTARTS   AGE
argocd-application-controller-xxx      1/1     Running   0          1m
argocd-dex-server-xxx                 1/1     Running   0          1m
argocd-redis-xxx                      1/1     Running   0          1m
argocd-repo-server-xxx                1/1     Running   0          1m
argocd-server-xxx                     1/1     Running   0          1m
```

---

## Phase 2: GitOps Setup

### Step 2.1: Update Repository URL (Forks Only)

If you're using a fork of this repository, update the repository URL:

```bash
# Edit the ConfigMap
vim k8s/bootstrap.yaml
```

Find and update:
```yaml
data:
  repo.url: https://github.com/YOUR-FORK/ai-sre-agent
```

### Step 2.2: Apply Bootstrap Manifests

```bash
kubectl apply -f k8s/bootstrap.yaml
```

### Step 2.3: Wait for ArgoCD Sync

```bash
# Watch ArgoCD application status
kubectl get application -n argocd -w
```

Wait until `STATUS` shows `Synced`:
```
NAME          SYNC STATUS   HEALTH STATUS
sre-lab-apps  Synced        Healthy
```

### Step 2.4: Verify Sync Status via CLI

```bash
argocd app list
```

If ArgoCD CLI is not installed:
```bash
brew install argocd-cli  # macOS
# or
kubectl exec -it deployment/argocd-server -n argocd -- argocd app list
```

---

## Phase 3: Container Images

### Step 3.1: Build the Application Image

```bash
docker build -t broken-app:v2 src/
```

Expected output:
```
[+] Building 15.3s (9/9) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 ...
 => naming to docker.io/library/broken-app:v2
```

### Step 3.2: Verify Image Exists

```bash
docker images | grep broken-app
```

Expected output:
```
broken-app   v2   a1b2c3d4e5f6   10 seconds ago   157MB
```

### Step 3.3: Load Image into Kind

```bash
kind load docker-image broken-app:v2 --name sre-lab
```

Expected output:
```
Image "broken-app:v2" loaded to node sre-lab-worker
Image "broken-app:v2" loaded to node sre-lab-worker2
Image "broken-app:v2" loaded to node sre-lab-control-plane
```

### Step 3.4: Pull and Load Ollama

```bash
docker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab
```

### Step 3.5: Verify Images in Kind

```bash
docker exec sre-lab-worker crictl images | grep -E "(broken-app|ollama)"
```

Expected output:
```
IMAGE                          TAG      IMAGE ID       SIZE
docker.io/broken-app           v2       a1b2c3d4e5f6   157MB
docker.io/ollama/ollama       latest   b2c3d4e5f6a7   1.2GB
```

---

## Phase 4: AI Engine

### Step 4.1: Wait for Ollama Deployment

```bash
kubectl rollout status deployment/ollama
```

Expected output:
```
Waiting for deployment "ollama" rollout to finish: 1 out of 1 new replicas have been updated...
deployment "ollama" successfully rolled out
```

### Step 4.2: Pull the AI Model

```bash
kubectl exec -it deployment/ollama -- ollama pull phi3
```

**Time estimate:** 3-10 minutes depending on internet speed.

Expected output:
```
pulling manifest for ollama/ollama:latest...
...
pulling a900614b75ab... 100%
...
success
```

### Step 4.3: Verify Model Downloaded

```bash
kubectl exec deployment/ollama -- ollama list
```

Expected output:
```
NAME      ID          SIZE      MODIFIED
phi3      a900614b75  2.4GB    10 seconds ago
```

---

## Phase 5: System Tuning

### Step 5.1: Apply Kernel Tuning

**⚠️ This step requires sudo privileges.**

```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512
```

### Step 5.2: Verify Tuning Applied

```bash
sysctl fs.inotify.max_user_watches
sysctl fs.inotify.max_user_instances
```

Expected output:
```
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 512
```

### Step 5.3: Make Tuning Persistent (Optional)

For permanent changes:

```bash
# Add to sysctl.conf
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
echo "fs.inotify.max_user_instances=512" | sudo tee -a /etc/sysctl.conf

# Apply without reboot
sudo sysctl -p
```

---

## Phase 6: Deploy Applications

### Step 6.1: Deploy Monitoring Stack

```bash
kubectl apply -f k8s/manifests/monitoring/
```

### Step 6.2: Verify Monitoring Deployment

```bash
kubectl get pods -n monitoring
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
grafana-xxx                   1/1     Running   0          30s
node-exporter-xxx             1/1     Running   0          30s
prometheus-xxx                1/1     Running   0          30s
```

### Step 6.3: Verify Prometheus Targets

```bash
# Port forward temporarily
kubectl port-forward svc/prometheus -n monitoring 9090:9090 &

# Check targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets'
```

You should see targets for:
- `kubernetes-apiservers`
- `kubernetes-nodes`
- `kubernetes-pods`
- `kubernetes-services`

### Step 6.4: Verify broken-app Deployment

```bash
kubectl get deployment broken-app
```

Expected output:
```
NAME          READY   UP-TO-DATE   AVAILABLE   AGE
broken-app    1/1     1            1           5m
```

---

## Phase 7: Run Agent

### Step 7.1: Create Agent ConfigMap

```bash
kubectl create configmap agent-code \
  --from-file=src/agent.py \
  --dry-run=client \
  -o yaml | kubectl apply -f -
```

### Step 7.2: Launch Agent Job

```bash
kubectl delete job sre-agent-job 2>/dev/null || true
kubectl apply -f k8s/agent-job.yaml
```

### Step 7.3: Watch Agent Execution

```bash
kubectl logs -l job-name=sre-agent-job -f
```

Expected output:
```
--- 🤖 AI SRE AGENT V3 (Secure) ---
🔌 Active Provider: OLLAMA
📡 Ollama URL: http://ollama-svc.default.svc.cluster.local:80/api/generate
🦙 Consulting Local LLM (phi3)...

📄 Captured Logs:
CRITICAL: Database Connection Timeout. Retrying...

--- 🧠 AI DIAGNOSIS ---
Based on the logs, the application is experiencing...

1. Error Type: Connection Timeout
2. Likely Cause: Database connection pool exhaustion
3. Recommended Fix: Increase connection pool size or optimize queries
-----------------------
```

---

## Verification

### Complete System Check

Run the environment check script:

```bash
make check
```

Expected output:
```
[1/8] Checking prerequisites... ✓
[2/8] Checking Docker... ✓
[3/8] Checking Kind cluster... ✓
[4/8] Checking Kubernetes nodes... ✓ (all Ready)
[5/8] Checking deployed namespaces... ✓ (all exist)
[6/8] Checking critical deployments... ✓ (all ready)
[7/8] Checking monitoring deployments... ✓ (all ready)
[8/8] Checking Docker images... ✓ (all loaded)
Check complete!
```

### Dashboard Verification

1. **ArgoCD:** https://localhost:8080
   - Verify `sre-lab-apps` shows `Synced` and `Healthy`

2. **Grafana:** http://localhost:3000
   - Navigate to Dashboards → Kubernetes Cluster Overview
   - Verify Node Status and Pod Count panels show data

3. **Prometheus:** http://localhost:9090
   - Run query: `up`
   - Verify all targets show `up`

---

## Troubleshooting

### "too many open files" Error

**Symptom:** Prometheus or Grafana pods in CrashLoopBackOff

**Solution:**
```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512

# Restart affected pods
kubectl rollout restart deployment prometheus -n monitoring
kubectl rollout restart deployment grafana -n monitoring
```

### Ollama Model Not Found

**Symptom:** Agent logs show "Model not found"

**Solution:**
```bash
kubectl exec -it deployment/ollama -- ollama pull phi3
```

### ImagePullBackOff

**Symptom:** Pod stuck in ImagePullBackOff

**Solution:**
```bash
# Rebuild and reload image
docker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab

# Restart deployment
kubectl rollout restart deployment broken-app
```

### ArgoCD Sync Error

**Symptom:** ArgoCD shows sync error

**Solution:**
```bash
# Check application status
kubectl get application sre-lab-apps -n argocd -o yaml

# View ArgoCD server logs
kubectl logs deployment/argocd-server -n argocd

# Manually sync
argocd app sync sre-lab-apps
```

### Agent Job Fails

**Symptom:** Agent job completes with error

**Solution:**
```bash
# Get job logs
kubectl logs job/sre-agent-job

# Get pod events
kubectl describe pod -l job-name=sre-agent-job

# Check if ollama is running
kubectl get pods -l app=ollama
```

---

## Cleanup

To destroy the entire lab:

```bash
cd terraform
terraform destroy --auto-approve
```

This will remove:
- Kind cluster (all nodes)
- ArgoCD installations
- All deployments and services

**Note:** Docker images remain on your host. To clean up:
```bash
docker rmi broken-app:v2 ollama/ollama:latest
kind delete cluster --name sre-lab
```
