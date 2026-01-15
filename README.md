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
