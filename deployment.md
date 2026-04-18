# 05 · Deploying on the Linux Server

*← [Index](../../INDEX.md) · [Docker](../04-containerization/docker.md)*

---

## Server Requirements

| Requirement | Value |
|---|---|
| OS | Ubuntu 24.04 LTS |
| RAM | Minimum 1 GB (2 GB recommended) |
| Disk | Minimum 5 GB free |
| CPU | Any 64-bit x86 |
| Access | SSH with sudo privileges |

This is the same server running the WordPress stack. The ML API runs as an isolated Docker container on a different port, so there is no conflict with Nginx or MariaDB.

---

## Step 1 — Prepare the Server

SSH into the server:

```bash
ssh your-user@your-server-ip
```

Update the package index and install prerequisites:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ca-certificates gnupg
```

---

## Step 2 — Install Docker on the Server

Docker is not in the default Ubuntu repositories. Install it from Docker's official repository:

```bash
# Add Docker's GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin

# Verify Docker is running
sudo systemctl status docker
```

Add the current user to the `docker` group to run Docker commands without `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version
docker run hello-world
```

---

## Step 3 — Copy the Project to the Server

**Option A — via SCP (simple transfer):**

From the local machine:

```bash
scp -r digit-recognizer-mlops/ your-user@your-server-ip:~/digit-api/
```

**Option B — via Git (recommended for ongoing development):**

```bash
# On the server
git clone https://github.com/your-username/digit-recognizer-mlops.git ~/digit-api
```

Using Git means future updates are a single `git pull` rather than another SCP transfer.

---

## Step 4 — Build the Docker Image on the Server

SSH into the server and navigate to the project:

```bash
cd ~/digit-api
docker build -t digit-api .
```

The first build will take 2–4 minutes as it downloads the base Python image and installs dependencies. Subsequent builds use cached layers and are much faster (under 30 seconds for code-only changes).

Verify the image was created:

```bash
docker images | grep digit-api
```

---

## Step 5 — Run the Container

```bash
docker run -d \
  --name digit-api \
  -p 8000:8000 \
  --restart unless-stopped \
  -v /var/log/digit-api:/app/logs \
  digit-api
```

Verify it started:

```bash
docker ps
docker logs digit-api --tail 20
```

Test from within the server:

```bash
curl http://localhost:8000/
```

Expected:

```json
{"status": "ok", "service": "digit-recognizer", "version": "1.0.0"}
```

At this point, the API is running and accessible on `localhost:8000`. It is not yet reachable from the internet — that requires Nginx.

---

## Step 6 — Configure UFW Firewall

Port 8000 should not be directly accessible from the internet. Only Nginx (on localhost) should reach it.

```bash
# Allow SSH (critical — do this first to avoid locking yourself out)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS for Nginx
sudo ufw allow 'Nginx Full'

# Enable the firewall
sudo ufw enable

# Verify rules
sudo ufw status numbered
```

Port 8000 is intentionally not listed in the UFW rules. Because Nginx communicates with Docker via `localhost:8000` (loopback interface), no explicit UFW rule is needed for this internal communication. External connections to port 8000 are blocked.

---

## Step 7 — Verify the Deployment

```bash
# Container is running
docker ps | grep digit-api

# Health check from server
curl -s http://localhost:8000/ | python3 -m json.tool

# Check logs
docker logs digit-api --tail 30

# Memory usage
docker stats digit-api --no-stream
```

---

## Updating the Deployed Service

When the model or code changes:

```bash
cd ~/digit-api

# Pull latest code (if using Git)
git pull

# Rebuild the image
docker build -t digit-api .

# Replace the running container
docker stop digit-api
docker rm digit-api
docker run -d \
  --name digit-api \
  -p 8000:8000 \
  --restart unless-stopped \
  -v /var/log/digit-api:/app/logs \
  digit-api
```

There is a brief downtime during `docker stop` and `docker run`. For zero-downtime deployments, a blue-green strategy (running two containers and switching Nginx upstream) would be needed — that is outside the scope of this project.

---

## Reboot Persistence

The `--restart unless-stopped` flag ensures the container restarts automatically:

- After the server reboots
- After the container process crashes
- After Docker daemon restarts

The container will not restart only if it was explicitly stopped with `docker stop`.

---

*→ Next: [06 · Nginx and HTTPS](../06-nginx-https/nginx-setup.md)*
