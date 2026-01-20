# 🏗️ System Architecture & Design Specification

> **Project:** Local AI-Driven SRE Observability Platform
> **Status:** Production-Ready (Lab Environment)
> **Author:** Baltazar Scotta

---

## 📋 Executive Summary
This document outlines the architectural decisions, system components, and data flow of the **AI-Driven SRE Lab**. The platform is designed to emulate a **Self-Healing, Air-Gapped Enterprise Environment** running on local hardware.

The core philosophy is **"GitOps First, AI Augmented."** No manual changes are allowed in the cluster; all state is defined in code, and operational diagnosis is delegated to an internal AI agent to minimize MTTR (Mean Time to Resolution).

---

## 🔭 High-Level Architecture

The system follows a **Hub-and-Spoke GitOps Pattern**, adapted for local execution. It strictly separates the **Control Plane** (ArgoCD), **Data Plane** (Workloads), and **Intelligence Plane** (AI Agent).

```mermaid
graph TD
    subgraph "Host Layer (Local Machine)"
        User[User / SRE]
        Terraform[Terraform CLI]
        Git[GitHub Repository]
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
        end
    end

    %% Flows
    User -->|Define IaC| Terraform
    Terraform -->|Provision| Kind
    User -->|Push Config| Git
    ArgoCD -->|Sync State (Pull)| Git
    ArgoCD -->|Apply Manifests| App & Ollama & Prom
    Prom -->|Scrape Metrics| App
    Agent -->|Fetch Logs| App
    Agent -->|Request Analysis (HTTP)| Ollama
    Ollama -->|Return Diagnosis| Agent
🧠 Architectural Decision Records (ADR)ADR-001: Infrastructure Provisioning StrategyDecision: Use Kind (Kubernetes in Docker) provisioned via Terraform.Alternatives Considered: Minikube, K3s, Manual kind create.Justification:Multi-Node Simulation: Kind allows us to simulate a realistic 3-node cluster (1 Control, 2 Workers) on a single machine, enabling testing of PodAntiAffinity and node failure scenarios.IaC Parity: Using Terraform (hashicorp/kubernetes provider) mimics the exact workflow used in AWS EKS / GCP GKE environments, creating a portable skill set.ADR-002: GitOps Delivery ModelDecision: Pull-Based GitOps using ArgoCD.Alternatives Considered: Push-Based (GitHub Actions -> kubectl apply).Justification:Security: The cluster does not expose its API credentials to the outside world. It reaches out to GitHub to fetch changes.Drift Detection: ArgoCD actively monitors the cluster state. If a human manually runs kubectl edit, ArgoCD detects the drift and can auto-heal the configuration, enforcing "Infrastructure as Code" integrity.ADR-003: AI Inference ArchitectureDecision: Internal Service Inference (Ollama running inside the cluster).Alternatives Considered: External API (OpenAI/Gemini), Host-based Ollama.Justification:Air-Gap Compliance: simulating a high-security environment (e.g., Banking/Healthcare) where sensitive logs cannot leave the VPC.Latency: The Agent communicates with the AI Model via the internal Cluster DNS (svc.cluster.local) over the container network (10Gbps+), eliminating internet latency and bandwidth costs.🔍 Data Flow & ObservabilityThe "Self-Healing" LoopMetric Collection: Prometheus scrapes the broken-app every 15s.Anomaly Detection: (Future Scope) Prometheus AlertManager triggers a webhook.Diagnosis: The AI Agent is triggered (currently manual, scalable to event-driven).It retrieves the last 50 lines of logs from the crashing pod.It constructs a prompt with system context.It sends the prompt to http://ollama-svc:80/api/generate.Resolution: The Agent outputs a structured Root Cause Analysis (RCA).🚧 Production Gap AnalysisComparing this Lab Environment vs. a Real Enterprise Production Setup.Component🏠 Lab Implementation🏢 Production Standard⚠️ Remediation for ProdStorageHostPath (Local Docker Disk)CSI (EBS / PersistentDisk)Use cloud storage classes to ensure data survives node termination.SecretsKubernetes Secrets (YAML)External Secrets OperatorIntegrate with AWS Secrets Manager or HashiCorp Vault. Never commit base64 secrets to Git.Ingresskubectl port-forwardIngress Controller + DNSDeploy Nginx/ALB Ingress Controller with external-dns and Cert-Manager for SSL.AI ComputeCPU Inference (Slow)GPU Node PoolUse Kubernetes Taints & Tolerations to pin AI workloads to GPU-accelerated nodes (NVIDIA).ScalingManual ReplicasHorizontal Pod Autoscaler (HPA)Implement HPA based on Custom Metrics (e.g., Request Rate) using KEDA.📚 Stack & VersionsKubernetes: v1.27 (Kind)Orchestrator: Terraform v1.5+GitOps: ArgoCD v2.10AI Engine: Ollama (running Phi-3 Mini 4k)Observability: Kube-Prometheus-Stack (Prometheus v2.45, Grafana v10.0)

