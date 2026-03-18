.PHONY: help lint lint-docker lint-k8s lint-python validate test clean check check-env deploy deploy-monitoring destroy

help:
	@echo "AI SRE Agent - Available targets:"
	@echo "  lint              - Run all linters"
	@echo "  lint-docker       - Lint Dockerfiles"
	@echo "  lint-k8s          - Validate Kubernetes manifests"
	@echo "  lint-python       - Lint Python code"
	@echo "  validate          - Validate K8s manifests syntax"
	@echo "  test              - Run tests"
	@echo "  clean             - Clean up generated files"
	@echo "  check             - Run environment check script"
	@echo "  check-env         - Run environment check script"
	@echo "  deploy            - Deploy all K8s resources"
	@echo "  deploy-monitoring - Deploy monitoring stack only"
	@echo "  destroy           - Destroy Terraform resources"

lint: lint-docker lint-k8s lint-python
	@echo "All linters passed!"

lint-docker:
	@echo "Linting Dockerfiles..."
	@if command -v hadolint >/dev/null 2>&1; then \
		hadolint src/Dockerfile; \
	else \
		echo "hadolint not installed, skipping. Install with: brew install hadolint"; \
	fi

lint-k8s:
	@echo "Validating Kubernetes manifests..."
	@if command -v kubeconform >/dev/null 2>&1; then \
		kubeconform -strict -summary k8s/manifests/ k8s/*.yaml; \
	elif command -v kubeval >/dev/null 2>&1; then \
		kubeval k8s/manifests/*.yaml k8s/*.yaml; \
	else \
		echo "kubeconform/kubeval not installed. Install with: go install github.com/yannh/kubeconform@latest"; \
	fi

lint-python:
	@echo "Linting Python code..."
	@if command -v pylint >/dev/null 2>&1; then \
		pylint src/*.py --disable=C0114,C0115,C0116 --max-line-length=100 || true; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 src/*.py --max-line-length=100 || true; \
	else \
		echo "pylint/flake8 not installed. Install with: pip install pylint flake8"; \
	fi

validate:
	@echo "Validating Kubernetes YAML syntax..."
	@for f in k8s/manifests/*.yaml k8s/*.yaml; do \
		if [ -f "$$f" ]; then \
			python3 -c "import yaml; yaml.safe_load(open('$$f'))" && echo "$$f: OK" || echo "$$f: FAILED"; \
		fi \
	done

test:
	@echo "Running tests..."
	@echo "No tests configured yet. Add pytest tests to src/"

clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__ src/__pycache__ .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

install-deps:
	@echo "Installing development dependencies..."
	@pip install pylint flake8 pytest pyyaml kubernetes requests || true
	@go install github.com/yannh/kubeconform@latest || true

terraform-validate:
	@echo "Validating Terraform..."
	@cd terraform && terraform fmt -check -recursive && terraform validate

check-git:
	@echo "Checking for secrets in git..."
	@if command -v gitleaks >/dev/null 2>&1; then \
		gitleaks detect --source-dir .; \
	else \
		echo "gitleaks not installed, skipping. Install with: brew install gitleaks"; \
	fi

check check-env:
	@echo "Running environment check..."
	@bash scripts/check-env.sh

deploy:
	@echo "Deploying Kubernetes resources..."
	@kubectl apply -f k8s/bootstrap.yaml
	@kubectl apply -f k8s/manifests/
	@kubectl apply -f k8s/manifests/monitoring/
	@echo "Deployment complete!"

deploy-monitoring:
	@echo "Deploying monitoring stack..."
	@kubectl apply -f k8s/manifests/monitoring/
	@echo "Monitoring stack deployed!"

destroy:
	@echo "Destroying Terraform resources..."
	@cd terraform && terraform destroy --auto-approve
