# 🤖 Agentic SRE: Automated Incident Triage System

**Role:** SRE & Observability Engineer
**Status:** Active Prototype
**Stack:** Kubernetes (Kind), Prometheus, Grafana, Python, Google Gemini AI

## 📖 Project Overview
This project bridges **Legacy Operations** with **Agentic AI**. I architected a self-healing infrastructure loop where an AI agent monitors real-time observability data from Prometheus and performs autonomous root-cause analysis (RCA) on Kubernetes pods.

### 🏗️ Architecture
1.  **Infrastructure:** Local K8s cluster (Kind) simulating a multi-node production environment.
2.  **Observability:** Full Prometheus & Grafana stack collecting Golden Signals (Latency, Traffic, Errors, Saturation).
3.  **Visuals:** Integrated Node Exporter Dashboard (ID 1860) for deep-dive cluster metrics.
4.  **AI Agent:** A custom Python controller that:
    * Detects anomalies via Prometheus API.
    * Extracts logs via Kubernetes API (kubectl).
    * Consults **Google Gemini LLM** for remediation strategies.

## 🚀 Key Features
* **Automated Triage:** Reduces MTTR by instantly analyzing stack traces with LLMs.
* **GitOps Workflow:** Fully containerized application with reproducible manifests.
* **Production Simulation:** Uses a "Broken App" microservice to generate random HTTP 500 errors for testing.

## 🛠️ How to Run
1.  **Bootstrap Cluster:**
    ```bash
    kind create cluster --config k8s/kind-config.yaml
    ```
2.  **Deploy Stack:**
    ```bash
    kubectl apply -f k8s/manifests/deployment.yaml
    helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack
    ```
3.  **Run Agent:**
    ```bash
    export GEMINI_API_KEY="your_key"
    python3 src/agent.py
    ```

---

## 🧠 Design Decisions & Roadmap
This section outlines the architectural choices made for this prototype and the path to a production-grade implementation.

### 1. Infrastructure Choice: Why Kind?
**Decision:** Selected **Kind (Kubernetes in Docker)** over Minikube or managed cloud providers (GKE/EKS).
* **Rationale:** Kind runs nodes as Docker containers, allowing for a lightweight simulation of a **multi-node cluster** on local hardware. This enables testing node-failure scenarios and pod rescheduling without the overhead of VMs or cloud costs.
* **Production Path:** For a live environment (50+ nodes), this agent would transition to a **DaemonSet** or **CronJob** running directly on the cluster, utilizing a `ServiceAccount` with restricted RBAC permissions instead of external API keys.

### 2. Handling Scale & Rate Limits
**Challenge:** Direct API calls to LLMs (Google Gemini) are subject to rate limits (HTTP 429) and can be overwhelmed by "Thundering Herd" scenarios (e.g., 200 pods crashing simultaneously).
* **Current State:** Basic retry logic.
* **Future Roadmap:**
    * Implement **Exponential Backoff** (jittered retries) to handle API throttling gracefully.
    * Decouple detection from analysis using a **Message Queue (Redis/RabbitMQ)**. The agent would push alerts to a queue, and a separate worker pool would process them asynchronously, ensuring the external API is never flooded.

### 3. Security & PII Compliance
**Challenge:** Sending raw logs to a public LLM poses a risk of leaking PII (Personally Identifiable Information) or secrets.
* **Mitigation Strategy:**
    * **Middleware Sanitization:** Implement a pre-processing layer using Regex to scrub sensitive patterns (Emails, IP addresses, API Keys) before the payload leaves the cluster.
    * **Private AI:** For highly regulated environments (Fintech/Health), replace Gemini with a self-hosted LLM (e.g., **Llama 3 via Ollama**) running within the VPC to ensure data sovereignty.
