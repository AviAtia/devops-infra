# devops-infra

Infrastructure repository for the DevOps challenge. Contains the Jenkins Docker setup, shared CI scripts, and the Helm chart that ArgoCD uses to deploy the Node.js app to Kubernetes (Minikube).

**App repo:** [AviAtia/sample-nodejs-devops](https://github.com/AviAtia/sample-nodejs-devops)  
**Docker Hub:** [avrahamatia/sample-nodejs](https://hub.docker.com/r/avrahamatic/sample-nodejs)

---

## Repository structure

```
devops-infra/
├── Dockerfile            # Jenkins image with Docker CLI, kubectl, Helm, Trivy, pylint
├── docker-compose.yml    # Runs Jenkins; mounts Docker socket + kubeconfig
├── plugins.txt           # Jenkins plugins list (installed at image build time)
├── Jenkinsfile           # PR gated pipeline for this repo (pylint + helm lint + dry-run)
├── ci-scripts/           # Shared CI scripts — cloned by every app pipeline
│   ├── sast.py           # Semgrep SAST scan
│   ├── build.py          # Docker build
│   ├── trivy_scan.py     # Trivy image vulnerability scan
│   ├── push_image.py     # Docker Hub push
│   ├── version_bump.py   # Patch version bump + git tag
│   ├── update_helm.py    # Update image tag in any GitOps values.yaml
│   └── pylint_check.py   # Pylint code quality check
└── helm/
    └── sample-nodejs/
        ├── Chart.yaml        # includes Prometheus as a dependency
        ├── Chart.lock        # pins exact Prometheus version
        ├── values.yaml       # image tag + Prometheus config
        └── templates/
            ├── deployment.yaml
            ├── service.yaml                   # has Prometheus scrape annotations
            ├── ingress.yaml
            ├── configmap.yaml
            ├── ingress-nginx-loadbalancer.yaml
            ├── argocd-loadbalancer.yaml
            └── _helpers.tpl
```

---

## Shared CI scripts

All pipeline logic lives in `ci-scripts/` so it can be reused across multiple app repositories. Each app's Jenkinsfile clones this repo at the start of every run and references the scripts via the `CI_SCRIPTS` environment variable:

```groovy
environment {
    CI_SCRIPTS = "devops-infra/ci-scripts"
}

stage('Checkout') {
    steps {
        checkout scm
        sh "git clone https://github.com/AviAtia/devops-infra.git devops-infra"
    }
}
```

| Script | Purpose | Key arguments |
|---|---|---|
| `sast.py` | Semgrep SAST scan via Docker | `--workspace` |
| `build.py` | Docker image build | `--image-name`, `--image-tag`, `--extra-tags` |
| `trivy_scan.py` | Trivy HIGH/CRITICAL image scan | `--image`, `--ignore-unfixed`, `--skip-dirs` |
| `push_image.py` | Docker Hub login + push | `--image-name`, `--image-tag`, `--username`, `--password` |
| `version_bump.py` | Bump patch version in `package.json`, commit + tag | `--git-user`, `--git-token`, `--repo` |
| `update_helm.py` | Update `tag:` in any `values.yaml` and push | `--repo`, `--image-tag`, `--values-path` |
| `pylint_check.py` | Pylint code quality check | `--path`, `--min-score` (default 7.0), `--fail-on-warnings` |

`update_helm.py` accepts `--values-path` (default: `helm/sample-nodejs/values.yaml`) so it works for any app's Helm chart without modification.

---

## Jenkins

### Start Jenkins

```bash
docker compose up -d
```

Jenkins runs on **http://localhost:9090**.

On first run, get the admin password:

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Jenkins image

The custom `Dockerfile` extends `jenkins/jenkins:lts-jdk17` and pre-installs:

- Docker CLI (for building and pushing images)
- `kubectl` (for potential cluster operations)
- Helm
- Trivy (image vulnerability scanner)

Plugins are installed from `plugins.txt` at image build time.

### Docker socket access

`docker-compose.yml` mounts `/var/run/docker.sock` into the Jenkins container so pipelines can run Docker commands without Docker-in-Docker. The container runs as `root` for socket access.

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - ~/.kube:/root/.kube:ro
  - ~/.minikube:/root/.minikube:ro
```

### Required credentials

Configure these in Jenkins → Manage Jenkins → Credentials:

| ID | Type | Used for |
|---|---|---|
| `dockerhub-credentials` | Username/Password | Push image to Docker Hub |
| `github-credentials` | Username/Password (PAT) | Version bump commit + Helm chart update |

PAT needs `repo` scope on GitHub.

### Pipelines

| Pipeline | Repo | Jenkinsfile | Trigger |
|---|---|---|---|
| App PR gated | `sample-nodejs-devops` | `ci/Jenkinsfile` | SCM polling on open PRs |
| App post-merge | `sample-nodejs-devops` | `ci/Jenkinsfile.main` | Commit to `main` |
| Infra PR gated | `devops-infra` | `Jenkinsfile` | SCM polling on open PRs |

The infra PR pipeline runs three checks on every PR to this repo:

| Stage | What it checks |
|---|---|
| Pylint | Code quality on `ci-scripts/` — fails below score 7.0 or on errors |
| Helm Lint | Chart structure, required fields, YAML syntax |
| Helm Dry Run | Renders templates and validates against the Kubernetes API schema |

Create a **Multibranch Pipeline** in Jenkins for each repo. Branch protection on `main` in both repos requires the respective status check to pass before merge:
- `sample-nodejs-devops` → requires `Jenkins CI/PR`
- `devops-infra` → requires `Jenkins CI/Infra PR`

---

## Helm chart

The `helm/sample-nodejs` chart deploys the Node.js app to Kubernetes.

### What it creates

| Resource | Details |
|---|---|
| Deployment | 1 replica, rolling update, non-root security context |
| Service | ClusterIP, port 80 → container 8080, Prometheus scrape annotations |
| Ingress | nginx ingress class, host `nodejsapp.local` |
| ConfigMap | `PORT=8080` environment variable |
| Prometheus | Deployed as a chart dependency — scrapes `/metrics` automatically |
| Ingress-nginx patch | Sets ingress-nginx-controller service to `LoadBalancer` type |
| ArgoCD patch | Sets argocd-server service to `LoadBalancer` type |

Probes: readiness on `GET /ready`, liveness on `GET /live`.

Resource limits: CPU 250m / Memory 256Mi. Requests: CPU 100m / Memory 128Mi.

### Prometheus

Prometheus is included as a Helm dependency — no separate installation needed. It discovers the app automatically via annotations on the Service:

```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "8080"
prometheus.io/path: "/metrics"
```

Access the Prometheus UI:

```bash
kubectl port-forward svc/sample-nodejs-prometheus-server 9090:80
# open http://localhost:9090
```

Search for `root_access_total` to see the app's custom metric.

> `charts/` is in `.gitignore` — ArgoCD downloads the prometheus chart automatically at sync time. `Chart.lock` is committed to pin the exact version.

### Key values

```yaml
image:
  repository: avrahamatia/sample-nodejs
  tag: "1.0.7"          # updated automatically by Jenkins after each merge

ingress:
  host: nodejsapp.local

prometheus:
  alertmanager:
    enabled: false       # not needed for local setup
  server:
    persistentVolume:
      enabled: false     # no PV needed in Minikube
```

### Manual deploy (without ArgoCD)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm dependency update helm/sample-nodejs
helm install sample-nodejs helm/sample-nodejs
# or upgrade
helm upgrade sample-nodejs helm/sample-nodejs
```

---

## ArgoCD (GitOps)

ArgoCD watches this repo and auto-syncs the Kubernetes cluster whenever `values.yaml` changes.

### Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Access the UI

The `argocd-server` service is patched to `LoadBalancer` type via `helm/sample-nodejs/templates/argocd-loadbalancer.yaml`, so no port-forward is needed. Open **https://localhost:8090** directly (requires `minikube tunnel` to be running).

Get the initial admin password:

```bash
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d
```

### ArgoCD Application config

Create an Application in ArgoCD pointing to:

- **Repo URL:** `https://github.com/AviAtia/devops-infra`
- **Path:** `helm/sample-nodejs`
- **Destination namespace:** `default`
- **Sync policy:** Automated

ArgoCD polls every 3 minutes (webhooks are not available in a local setup).

---

## Startup sequence (after Docker Desktop restart)

Run these steps in order every time Docker Desktop or Minikube is restarted:

```bash
# 1. Start Minikube
minikube start

# 2. Start Jenkins
cd /Users/sabav/personalWork/devops-infra
docker compose up -d

# 3. Start Minikube tunnel — keep this terminal open
sudo minikube tunnel
```

- **ArgoCD** → https://localhost:8090
- **App** → http://nodejsapp.local/my-app
- **Jenkins** → http://localhost:9090

> **Why tunnel?** Both the ingress-nginx-controller and argocd-server services are type `LoadBalancer`. On Mac with the Docker driver, they only get an external IP (`127.0.0.1`) while `minikube tunnel` is running. Without it, services stay `<pending>` and ArgoCD shows them as **Progressing** indefinitely.

## Shutdown sequence

```bash
# 1. Stop minikube tunnel — Ctrl+C in the terminal running it

# 2. Stop Jenkins
cd /Users/sabav/personalWork/devops-infra
docker compose stop

# 3. Stop Minikube
minikube stop
```

---

## Accessing the app (Minikube + Mac Docker driver)

```bash
# /etc/hosts — add once
echo "127.0.0.1 nodejsapp.local" | sudo tee -a /etc/hosts
```

Then open **http://nodejsapp.local/my-app** in the browser.

Confirm the tunnel is working:
```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
# EXTERNAL-IP should show 127.0.0.1, not <pending>
```
