# Two-Tier Flask + MySQL Deployment on Kubernetes (KIND)

## Project Overview

A fintech startup's personal expense tracking platform, deployed as a **two-tier architecture**:

- **Tier 1 (Frontend/App):** Flask web application
- **Tier 2 (Backend/Data):** MySQL database

Deployed on a **KIND (Kubernetes IN Docker)** cluster running inside an **AWS EC2** instance — a cost-effective alternative to AWS EKS for PoC purposes.

---

## Architecture

```
                    [ User Browser ]
                          │
                    http://EC2_IP:5000
                          │
                ┌─────────────────────┐
                │   EC2 Instance       │
                │  (Ubuntu t2.medium)  │
                │                      │
                │  ┌────────────────┐  │
                │  │  Docker Engine │  │
                │  │  ┌──────────┐  │  │
                │  │  │   KIND   │  │  │
                │  │  │ Cluster  │  │  │
                │  │  └──────────┘  │  │
                │  └────────────────┘  │
                └─────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        │        Kubernetes Cluster            │
        │                                       │
        │  ┌──────────────┐  ┌──────────────┐ │
        │  │  Namespace:   │  │  Namespace:   │ │
        │  │  flask-app    │  │  mysql-db     │ │
        │  │               │  │               │ │
        │  │ Deployment    │  │ Deployment    │ │
        │  │ (flask pod)   │  │ (mysql pod)   │ │
        │  │      │        │  │      │        │ │
        │  │  Service      │──┼──▶Service      │ │
        │  │  (NodePort    │  │  (ClusterIP   │ │
        │  │   30007)      │  │   3306)       │ │
        │  └──────────────┘  └──────────────┘ │
        └───────────────────────────────────────┘
```

---

## Project Structure

```
Two-tier-application-K8S-KIND/
│
├── app.py                     # Flask app
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image definition
│
├── k8s-manifests/
│   ├── namespaces/
│   │   ├── flask-app.yaml
│   │   └── mysql-db.yaml
│   ├── flask-deployment.yaml  # Flask Deployment + Service
│   └── mysql-deployment.yaml  # MySQL Deployment + Service
│
├── kind-config.yaml           # KIND cluster config
│
└── README.md                  # This file
```

---

## Prerequisites

- AWS Account
- Ubuntu 22.04 EC2 instance (t2.medium — 2 vCPU, 4GB RAM minimum)
- DockerHub account (for pushing custom Flask image)

---

## Step-by-Step Deployment Guide

### Step 1: Launch EC2 Instance

1. AWS Console → EC2 → Launch Instance
2. Configuration:
   ```
   Name: kind-two-tier-ec2
   AMI: Ubuntu 22.04 LTS
   Instance type: t2.medium (2 vCPU, 4GB RAM)
   ```
3. Security Group — allow inbound ports:
   ```
   22    → SSH
   80    → HTTP
   5000  → Flask app
   3306  → MySQL (if needed)
   ```
4. Create/select a key pair and download the `.pem` file.
5. Connect via SSH:
   ```bash
   chmod 400 mykey.pem
   ssh -i mykey.pem ubuntu@<EC2_PUBLIC_IP>
   ```

---

### Step 2: Install Docker

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

Install MySQL client dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3-dev default-libmysqlclient-dev build-essential pkg-config
```

---

### Step 3: Install kubectl and KIND

**kubectl:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/kubectl
kubectl version --client
```

**KIND:**
```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind version
```

---

### Step 4: Create KIND Cluster

Create `kind-config.yaml`:
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
# Control plane node
- role: control-plane
  image: kindest/node:v1.28.0
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 30007
    hostPort: 30007
    protocol: TCP
# Worker node 1
- role: worker
  image: kindest/node:v1.28.0
# Worker node 2
- role: worker
  image: kindest/node:v1.28.0
```

Create the cluster:
```bash
kind create cluster --name two-tier-cluster --config kind-config.yaml
kubectl cluster-info
kubectl get nodes
```

---

### Step 5: Create Namespaces

```bash
kubectl create namespace flask-app
kubectl create namespace mysql-db
kubectl get ns
```

---

### Step 6: Build & Push Flask Docker Image

```bash
git clone https://github.com/nasirbloch323/two-tier-app.git
cd two-tier-app/app

docker build -t <dockerhub-username>/flask-two-tier:latest .
docker login
docker push <dockerhub-username>/flask-two-tier:latest
cd ..
```

> MySQL uses the official `mysql:8` image directly — no custom build needed.

---

### Step 7: Kubernetes Manifests

**mysql-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-deployment
  namespace: mysql-db
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: rootpassword
        ports:
        - containerPort: 3306
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
  namespace: mysql-db
spec:
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
  type: ClusterIP
```

**flask-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-deployment
  namespace: flask-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flask
  template:
    metadata:
      labels:
        app: flask
    spec:
      containers:
      - name: flask
        image: <dockerhub-username>/flask-two-tier:latest
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: flask-service
  namespace: flask-app
spec:
  selector:
    app: flask
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30007
  type: NodePort
```

---

### Step 8: Deploy to Cluster

```bash
kubectl apply -f k8s-manifests/mysql-deployment.yaml
kubectl apply -f k8s-manifests/flask-deployment.yaml

kubectl get pods -n mysql-db
kubectl get pods -n flask-app
kubectl get svc -n mysql-db
kubectl get svc -n flask-app
```

---

### Step 9: Access the Application

```bash
kubectl port-forward svc/flask-service 5000:5000 -n flask-app --address 0.0.0.0
```

Open in browser:
```
http://<EC2_PUBLIC_IP>:5000
```

---

## Security Notes (Recommended Improvement)

Currently the MySQL password is stored as plain text in the deployment YAML. For production-grade security, use a **Kubernetes Secret** instead:

```bash
kubectl create secret generic mysql-secret \
  --from-literal=MYSQL_ROOT_PASSWORD=rootpassword -n mysql-db
```

Then reference it in the deployment:
```yaml
env:
- name: MYSQL_ROOT_PASSWORD
  valueFrom:
    secretKeyRef:
      name: mysql-secret
      key: MYSQL_ROOT_PASSWORD
```

---

## Troubleshooting

**Error: `connection to the server 127.0.0.1:XXXXX was refused`**

Cluster context is missing or the cluster is down:
```bash
docker ps                                    # check if KIND containers are running
kubectl config get-contexts                  # check available contexts
kubectl config use-context kind-two-tier-cluster
kubectl cluster-info
```

If containers aren't running, recreate the cluster:
```bash
kind create cluster --name two-tier-cluster --config kind-config.yaml
```

**Pods stuck in `Pending` or `CrashLoopBackOff`:**
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

---

## Conclusion

This project demonstrates a cost-effective two-tier Kubernetes deployment PoC using KIND on EC2 — covering cluster setup, namespace isolation, Deployments, Services (ClusterIP vs NodePort), and a path toward secure credential management with Kubernetes Secrets.
