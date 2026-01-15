# 1. Create the Cluster (Infrastructure Layer)
resource "kind_cluster" "sre_lab" {
  name           = "sre-lab"
  node_image     = "kindest/node:v1.27.3"
  wait_for_ready = true

  kind_config {
    kind = "Cluster"
    # FIXED: Changed from 'apiVersion' to 'api_version'
    api_version = "kind.x-k8s.io/v1alpha4"
    
    # Control Plane
    node {
      role = "control-plane"
      kubeadm_config_patches = [
        "kind: InitConfiguration\nnodeRegistration:\n  kubeletExtraArgs:\n    node-labels: \"ingress-ready=true\"\n"
      ]
      # Map ports for accessing apps from localhost
      extra_port_mappings {
        container_port = 80
        host_port      = 80
      }
    }

    # Worker Nodes
    node { role = "worker" }
    node { role = "worker" }
  }
}

# 2. Bootstrap ArgoCD (Platform Layer)
resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = "argocd"
  create_namespace = true
  version    = "5.46.7"

  depends_on = [kind_cluster.sre_lab]

  # Configuration values (Optimized for Lab)
  set {
    name  = "server.service.type"
    value = "ClusterIP"
  }
  set {
    name  = "redis.ha.enabled"
    value = "false"
  }
  set {
    name  = "controller.replicas"
    value = "1"
  }
  set {
    name  = "repoServer.replicas"
    value = "1"
  }
  set {
    name  = "server.replicas"
    value = "1"
  }
}

output "cluster_endpoint" {
  value = kind_cluster.sre_lab.endpoint
}
