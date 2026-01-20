🤖 Local AI-Driven SRE Observability LabA production-grade, air-gapped Kubernetes platform running entirely on your local machine.📖 IntroductionWelcome! This repository demonstrates how to build a Self-Healing, AI-Integrated Platform from scratch. It is designed to simulate a real-world Site Reliability Engineering (SRE) environment.What you will build:Infrastructure: A Kubernetes cluster running locally inside Docker (using Kind).Automation: A GitOps pipeline (using ArgoCD) that automatically syncs code changes to the cluster.Observability: A full monitoring stack (Prometheus & Grafana) to track CPU, RAM, and error rates.Artificial Intelligence: A local Large Language Model (Phi-3 running via Ollama) that lives inside the cluster.The Agent: A Python-based "AI Detective" that reads cluster logs and diagnoses crashes automatically.🛠️ Prerequisites (Start Here)Before running the lab, ensure you have these tools installed.ToolPurposeCheck InstallationDockerRuns the virtual nodesdocker versionTerraformCreates the infrastructureterraform -versionKubectlTalks to the clusterkubectl version --clientKindThe local cluster toolkind versionGitManages the codegit --versionNote: This lab requires a machine with at least 16GB RAM and 4 CPU Cores to run the AI models smoothly.🚀 Step 1: Clone & SetupFirst, get the code and prepare your workspace.Bash# 1. Clone the repository
git clone <YOUR_REPO_URL_HERE>
cd sre-lab

# 2. Make the scripts executable
chmod +x src/agent.py
🏗️ Step 2: Build the Infrastructure (Terraform)We use Terraform to automate the creation of the cluster. This ensures that every time you run this, you get the exact same environment.Initialize Terraform:Bashcd terraform
terraform init
Create the Cluster:Bashterraform apply --auto-approve
(This may take 2-3 minutes. It will download Docker images and start the Kind cluster nodes.)✅ Sanity Check:Run this command to confirm your cluster is alive:Bashkubectl get nodes
You should see 3 nodes: sre-lab-control-plane, sre-lab-worker, and sre-lab-worker2.🔄 Step 3: Install the "Brain" (ArgoCD)We use ArgoCD for "GitOps". This means ArgoCD watches this GitHub repository and automatically installs any Kubernetes manifests it finds.Return to the root folder:Bashcd ..
Apply the Bootstrap Config:Bashkubectl apply -f k8s/bootstrap.yaml
✅ Sanity Check:Wait about 60 seconds, then run:Bashkubectl get pods -n argocd
You should see several pods (like argocd-server, argocd-repo-server) with status Running.🐳 Step 4: Build & Load the ApplicationBecause this is a "Local" cluster, it cannot pull images from your laptop's hard drive directly. We must "Side-load" them into the cluster nodes.Build the Python Application:We are building version 2 (v2), which uses a production-ready Gunicorn server.Bashdocker build -t broken-app:v2 src/
Load the App into the Cluster:Bashkind load docker-image broken-app:v2 --name sre-lab
Load the AI Engine (Ollama):We pull the AI server image once and load it, so the cluster doesn't try to download 5GB over the internet repeatedly.Bashdocker pull ollama/ollama:latest
kind load docker-image ollama/ollama:latest --name sre-lab
🧠 Step 5: Initialize the Local AINow we need to download the actual "Brain" (the Language Model) into the persistent storage of our cluster.Wait for Ollama to start:Run this loop until you see the ollama pod is Running:Bashkubectl get pods -l app=ollama -w
(Press Ctrl+C once it says Running).Download the Phi-3 Model:This runs the command inside the pod to fetch the model files.Bashkubectl exec -it deployment/ollama -- ollama pull phi3
(This downloads ~2.4GB. It only needs to be done once.)⚙️ Step 6: Critical System Tuning (Do Not Skip!)This lab runs Heavy workloads (Prometheus, Grafana, AI). Standard laptop settings usually block this much activity. We need to increase the Linux file watcher limits.Run these commands on your host terminal:Bash# 1. Increase File Watchers (Prevents "Too Many Open Files" error)
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=512

# 2. (Optional) Make it permanent across reboots
echo "fs.inotify.max_user_watches = 524288" | sudo tee -a /etc/sysctl.conf
echo "fs.inotify.max_user_instances = 512" | sudo tee -a /etc/sysctl.conf
🕵️ Step 7: Run the AI SRE DetectiveNow for the magic. We will launch a Kubernetes Job. This job creates a temporary pod inside the cluster that:Talks to the Kubernetes API to fetch logs.Talks to the internal Ollama Service to analyze them.Prints a diagnosis.Upload the Detective Script:Bashkubectl create configmap agent-code --from-file=src/agent.py --dry-run=client -o yaml | kubectl apply -f -
Run the Job:Bash# Clean up any old runs
kubectl delete job sre-agent-job 2>/dev/null || true

# Start the Detective
kubectl apply -f k8s/agent-job.yaml
View the Results:Bashkubectl logs -l job-name=sre-agent-job -f
🧪 Experiments to TryNow that the platform is stable, try breaking it to see if the AI catches you!Experiment A: The Developer MistakeOpen src/Dockerfile.Change the last line to: CMD ["python", "app.py"] (The weak Dev Server).Rebuild and load the image:Bashdocker build -t broken-app:v2 src/
kind load docker-image broken-app:v2 --name sre-lab
kubectl rollout restart deployment broken-app
Run the Agent Job again. It should warn you about using a Development Server.Experiment B: The Memory LeakEdit k8s/manifests/broken-app.yaml.Change resources.limits.memory to 10Mi (Too small).Push to Git (or apply locally).Watch the pods crash (OOMKilled).Run the Agent Job. It should diagnose an Out Of Memory error.🧹 CleanupWhen you are finished, remove the entire lab to free up your CPU and RAM.Bashcd terraform
terraform destroy --auto-approve
🆘 TroubleshootingError: connection refused or dial tcpCause: The cluster isn't running or the kubectl context is wrong.Fix: Run kubectl get nodes. If that fails, run terraform apply again.Error: failed to create fsnotify watcher: too many open filesCause: Your laptop hit the file watch limit (common with Prometheus/Grafana).Fix: Re-run the commands in Step 6.Error: Ollama Connection Error: Read timed outCause: Your CPU is overloaded.Fix: Scale down the monitoring stack to free up resources:Bashkubectl scale deployment -n monitoring --replicas=0 --all
kubectl scale statefulset -n monitoring --replicas=0 --all
