🏗️ Architecture & Design Decisions"The difference between a script and a platform is intention."This document details the architectural choices, trade-offs, and production gaps considered during the engineering of this Local SRE Observability Lab.📐 High-Level ArchitectureThe platform follows a Hub-and-Spoke GitOps Pattern, adapted for a local air-gapped environment.Code snippetgraph TD
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
            Grafana[Grafana]
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
🧠 Design Decision Records (DDR)1. Infrastructure: Why Kind (Kubernetes in Docker)?The Choice: Kind over Minikube or K3s.The "Why": Kind runs nodes as Docker containers. This allows us to simulate a Multi-Node Cluster (1 Control Plane, 2 Workers) on a single laptop. This is critical for testing PodAntiAffinity, Taints/Tolerations, and node-failure scenarios that single-node setups (Minikube) cannot replicate.The Trade-off: Kind has higher overhead than K3s but offers a more authentic "Vanilla Kubernetes" API experience, matching standard EKS/GKE environments.2. Delivery: Why Pull-Based GitOps (ArgoCD)?The Choice: ArgoCD watching the repo vs. GitHub Actions pushing kubectl apply.The "Why": Security and Drift Detection.Security: The cluster does not need to expose its API credentials to GitHub. The cluster reaches out to fetch changes (Pull Model).Drift: If someone manually edits a deployment (e.g., kubectl edit), ArgoCD immediately detects the configuration drift and can auto-heal it.The "Production" View: In a real setup, this prevents "Snowflake Servers" where manual changes are lost during the next deployment.3. AI Architecture: Why an Internal Kubernetes Job?The Choice: An ephemeral Batch/v1 Job running inside the cluster vs. a script running on the Host.The "Why":Latency: The agent talks to the Ollama Service via the internal Cluster DNS (svc.cluster.local) over the container network (10Gbps+), avoiding the slow and fragile kubectl port-forward tunnel.Security: We use a Kubernetes ServiceAccount with strictly scoped RBAC permissions (Read Logs) rather than using a global Admin kubeconfig.The Trade-off: Debugging is harder because you can't see "print" statements instantly; you must tail the job logs.🚧 Production Gap Analysis"If we were deploying this to AWS/GCP tomorrow, what would change?"ComponentCurrent Implementation (Lab)Production Standard (AWS/GCP)Why Change?StorageHostPath (Local Disk)EBS / PersistentDisk (CSI)Local disk dies with the node. Cloud block storage replicates data across Availability Zones.IngressPort-ForwardIngress Controller (Nginx/ALB) + DNSPort-forwarding is manual and brittle. Production needs stable DNS (e.g., app.company.com) and TLS termination.SecretsPlaintext YAMLExternal Secrets Operator (Vault/AWS SM)Never commit passwords to Git. We would inject secrets at runtime from a secure vault.AI EngineLocal CPU InferenceDedicated GPU Node PoolCPU inference blocks the node. Production would use Taints/Tolerations to pin AI workloads to GPU-accelerated nodes.ScalingManual replicas: 1HPA (Horizontal Pod Autoscaler)Production traffic varies. HPA would scale pods based on CPU/Memory metrics automatically.🔬 The "Senior" Troubleshooting LogicScenario: The "Too Many Open Files" CrashDuring the development of the observability stack, we encountered a failed to create fsnotify watcher error.Root Cause: The default Linux kernel limit (fs.inotify.max_user_watches) is often set to 8,192.The Impact: Prometheus opens thousands of file descriptors to track metrics. ArgoCD watches thousands of Git objects. We exhausted the OS limit.The Fix: Tuned the kernel via sysctl to 524288 watches, allowing the "Enterprise" stack to breathe on consumer hardware.Scenario: The OOM (Out of Memory) LoopThe Python application (v2) utilized Gunicorn with 4 sync workers (-w 4).Root Cause: Each worker consumed ~60MB RAM. The combined footprint exceeded the Kind node's implicit allocation.The Symptom: Kubernetes OOMKilled status; Exit Code 137.The Fix: Implemented resources.limits in the Deployment manifest to strictly cap memory at 256Mi, forcing the scheduler to reject the pod or kill it gracefully before it destabilized the node.
