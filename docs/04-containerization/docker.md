# 04 · Docker

*← [Index](../../INDEX.md) · [FastAPI Service](../03-api-layer/fastapi-service.md)*

---

## Why Docker for an ML Service

Running the API in a Docker container solves a problem that every ML project eventually hits: the environment.

The neural network depends on a specific version of NumPy. FastAPI depends on a specific version of Pydantic. Uvicorn has its own requirements. On a local machine, these can be managed with a virtualenv. On a remote server, recreating that exact environment manually is error-prone and fragile.

Docker bakes the application code, the Python interpreter, and all dependencies into a single image. That image runs identically on a laptop, a CI server, or a production machine. The container is the unit of deployment.

---

## Project File Layout

```
digit-recognizer-mlops/
├── Dockerfile
└── app/
    ├── main.py
    ├── model.pkl
    └── requirements.txt
```

Everything Docker needs is in this tree. The `Dockerfile` sits at the root.

---

## `Dockerfile`

```dockerfile
# ── Base image ──────────────────────────────────────────────────────────
# Use the official slim Python image. "slim" omits build tools and
# documentation, reducing the final image size significantly.
FROM python:3.11-slim

# ── Working directory ───────────────────────────────────────────────────
# All subsequent commands run from /app inside the container.
# This is also where the application files will live.
WORKDIR /app

# ── Install dependencies first (layer caching) ─────────────────────────
# Copy requirements.txt before the application code. Docker caches each
# layer. If requirements.txt hasn't changed, this pip install layer is
# reused from cache — making rebuilds after code changes much faster.
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application files ──────────────────────────────────────────────
# model.pkl and main.py are copied after dependencies. This preserves
# the cache benefit above — a code-only change doesn't re-run pip.
COPY app/main.py .
COPY app/model.pkl .

# ── Expose the application port ─────────────────────────────────────────
# This is documentation for Docker — it does not actually publish the
# port. Port binding happens at `docker run` time with -p.
EXPOSE 8000

# ── Start the API server ────────────────────────────────────────────────
# Run Uvicorn as the process. No --reload in production.
# 0.0.0.0 is required so the container is reachable from outside itself.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Layer Caching — Why the Order Matters

Docker builds images layer by layer, and each layer is cached. If a layer's input hasn't changed, Docker reuses the cached version.

By copying `requirements.txt` and running `pip install` before copying the application code, we ensure that:

- A change to `main.py` only triggers the `COPY main.py` layer and beyond — the expensive `pip install` is skipped
- A change to `requirements.txt` correctly invalidates the install layer and re-runs pip

This is a standard Docker optimization. Without it, every code change would re-download and re-install all packages.

---

## Building the Image

From the project root (where the `Dockerfile` is):

```bash
docker build -t digit-api .
```

- `-t digit-api` tags the image with the name `digit-api`
- `.` is the build context — Docker sends this directory to the build daemon

To confirm the image was created:

```bash
docker images | grep digit-api
```

---

## Running the Container

```bash
docker run -d \
  --name digit-api \
  -p 8000:8000 \
  --restart unless-stopped \
  digit-api
```

| Flag | Meaning |
|---|---|
| `-d` | Run in detached mode (background) |
| `--name digit-api` | Assign a name so it can be referenced by name |
| `-p 8000:8000` | Map host port 8000 to container port 8000 |
| `--restart unless-stopped` | Auto-restart if the process crashes or the server reboots |
| `digit-api` | The image to run |

---

## Verifying the Container is Running

```bash
# Check container status
docker ps

# Check logs (last 50 lines)
docker logs digit-api --tail 50

# Follow live logs
docker logs -f digit-api

# Test the health endpoint from inside the server
curl http://localhost:8000/
```

Expected output from the health check:

```json
{"status": "ok", "service": "digit-recognizer", "version": "1.0.0"}
```

---

## Mounting a Log Volume (Optional but Recommended)

By default, the `predictions.log` file written by the application lives inside the container's filesystem. If the container is removed and recreated, those logs are lost.

To persist logs on the host:

```bash
docker run -d \
  --name digit-api \
  -p 8000:8000 \
  --restart unless-stopped \
  -v /var/log/digit-api:/app \
  digit-api
```

This mounts the host directory `/var/log/digit-api` to `/app` inside the container. `predictions.log` will be written there and survive container restarts and replacements.

Create the host directory first:

```bash
sudo mkdir -p /var/log/digit-api
sudo chown $USER /var/log/digit-api
```

---

## Common Docker Commands Reference

| Command | Purpose |
|---|---|
| `docker build -t digit-api .` | Build the image |
| `docker run -d -p 8000:8000 digit-api` | Start the container |
| `docker ps` | List running containers |
| `docker logs digit-api` | View container logs |
| `docker logs -f digit-api` | Follow live logs |
| `docker stop digit-api` | Stop the container |
| `docker start digit-api` | Restart a stopped container |
| `docker rm digit-api` | Remove the container |
| `docker rmi digit-api` | Remove the image |
| `docker exec -it digit-api bash` | Open a shell inside the container |

---

## Rebuilding After a Code Change

```bash
# Stop and remove the old container
docker stop digit-api
docker rm digit-api

# Rebuild the image
docker build -t digit-api .

# Run the new container
docker run -d \
  --name digit-api \
  -p 8000:8000 \
  --restart unless-stopped \
  digit-api
```

---

*→ Next: [05 · Server Deployment](../05-server-deployment/deployment.md)*
