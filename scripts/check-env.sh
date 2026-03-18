#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "  AI SRE Agent - Environment Checker"
echo "========================================"
echo ""

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        return 1
    fi
}

check_version() {
    local cmd=$1
    local min_version=$2
    local flag=${3:---version}
    local current
    current=$($cmd $flag 2>/dev/null | head -n1 || echo "0")
    echo "  $cmd version: $current (required: >= $min_version)"
}

echo -e "${YELLOW}[1/8] Checking prerequisites...${NC}"
MISSING=0

check_command docker || ((MISSING++))
check_command terraform || ((MISSING++))
check_command kubectl || ((MISSING++))
check_command kind || ((MISSING++))
check_command git || ((MISSING++))

if [ $MISSING -gt 0 ]; then
    echo -e "\n${RED}Missing $MISSING required commands. Please install them before continuing.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2/8] Checking Docker...${NC}"
if docker ps >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running. Start Docker and try again."
    exit 1
fi

echo ""
echo -e "${YELLOW}[3/8] Checking Kind cluster...${NC}"
if kind get clusters 2>/dev/null | grep -q "sre-lab"; then
    echo -e "${GREEN}✓${NC} Kind cluster 'sre-lab' exists"
    kubectl cluster-info --context kind-sre-lab >/dev/null 2>&1 && echo -e "${GREEN}✓${NC} Cluster is accessible" || echo -e "${RED}✗${NC} Cluster is not accessible"
else
    echo -e "${RED}✗${NC} Kind cluster 'sre-lab' does not exist"
    echo "  Run: cd terraform && terraform apply"
fi

echo ""
echo -e "${YELLOW}[4/8] Checking Kubernetes nodes...${NC}"
if kubectl get nodes >/dev/null 2>&1; then
    kubectl get nodes --no-headers | while read line; do
        node=$(echo $line | awk '{print $1}')
        status=$(echo $line | awk '{print $2}')
        if [ "$status" = "Ready" ]; then
            echo -e "${GREEN}✓${NC} Node $node is Ready"
        else
            echo -e "${RED}✗${NC} Node $node is $status"
        fi
    done
else
    echo -e "${RED}✗${NC} Cannot access Kubernetes cluster"
fi

echo ""
echo -e "${YELLOW}[5/8] Checking deployed namespaces...${NC}"
NAMESPACES=("default" "argocd" "monitoring")
for ns in "${NAMESPACES[@]}"; do
    if kubectl get namespace "$ns" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Namespace '$ns' exists"
    else
        echo -e "${YELLOW}!${NC} Namespace '$ns' does not exist (may not be deployed yet)"
    fi
done

echo ""
echo -e "${YELLOW}[6/8] Checking critical deployments...${NC}"
DEPLOYMENTS=("broken-app" "ollama")
for deploy in "${DEPLOYMENTS[@]}"; do
    if kubectl get deployment "$deploy" -n default >/dev/null 2>&1; then
        ready=$(kubectl get deployment "$deploy" -n default -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        desired=$(kubectl get deployment "$deploy" -n default -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "?")
        if [ "$ready" = "$desired" ] && [ "$ready" != "0" ]; then
            echo -e "${GREEN}✓${NC} Deployment $deploy is ready ($ready/$desired)"
        else
            echo -e "${YELLOW}!${NC} Deployment $deploy is not ready ($ready/$desired)"
        fi
    else
        echo -e "${YELLOW}!${NC} Deployment $deploy not found"
    fi
done

echo ""
echo -e "${YELLOW}[7/7] Checking monitoring deployments...${NC}"
MONITORING_DEPLOYMENTS=("prometheus" "grafana" "node-exporter")
for deploy in "${MONITORING_DEPLOYMENTS[@]}"; do
    if kubectl get deployment "$deploy" -n monitoring >/dev/null 2>&1; then
        ready=$(kubectl get deployment "$deploy" -n monitoring -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        desired=$(kubectl get deployment "$deploy" -n monitoring -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "?")
        if [ "$ready" = "$desired" ] && [ "$ready" != "0" ]; then
            echo -e "${GREEN}✓${NC} Monitoring $deploy is ready ($ready/$desired)"
        else
            echo -e "${YELLOW}!${NC} Monitoring $deploy is not ready ($ready/$desired)"
        fi
    else
        echo -e "${YELLOW}!${NC} Monitoring $deploy not found"
    fi
done

echo ""
echo -e "${YELLOW}[7/8] Checking Docker images...${NC}"
IMAGES=("broken-app:v2" "ollama/ollama:latest")
for img in "${IMAGES[@]}"; do
    if docker image inspect "$img" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Image $img is available"
    else
        echo -e "${YELLOW}!${NC} Image $img not found locally"
        if [[ "$img" == "broken-app:v2" ]]; then
            echo "  Run: docker build -t broken-app:v2 src/"
        fi
    fi
done

echo ""
echo "========================================"
echo -e "${GREEN}Check complete!${NC}"
echo "========================================"

echo ""
echo "Quick commands:"
echo "  ArgoCD:     kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "  Grafana:    kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80"
echo "  Prometheus: kubectl port-forward svc/prometheus -n monitoring 9090:9090"
echo "  Run agent:  kubectl apply -f k8s/agent-job.yaml"
