# Index — Digit Recognizer MLOps Documentation

> Complete documentation index. Each section is a standalone document that can be read independently.

*← [README](README.md)*

---

## Part I — Foundation

### [01 · Project Architecture](docs/01-project-overview/architecture.md)

- System architecture diagram
- Component responsibilities
- Technology choices and rationale
- Port map and service boundaries

---

## Part II — The Model

### [02 · The Neural Network](docs/02-base-model/neural-network.md)

- Network architecture (`784 → 128 → 64 → 10`)
- Mathematical foundations (forward pass, backprop, He initialization)
- Training configuration (batch size, learning rate, epochs)
- Achieved accuracy on MNIST test set
- How the model is saved to `model.pkl`
- Loading the model for inference

---

## Part III — The API

### [03 · FastAPI Service](docs/03-api-layer/fastapi-service.md)

- Why FastAPI
- Application structure (`main.py`)
- Startup: loading the model once into memory
- Endpoints
  - `GET /` — health check
  - `POST /predict` — digit prediction
- Request and response schemas (Pydantic)
- Running locally with Uvicorn
- Testing via `/docs` (Swagger UI)
- Input validation and error handling

---

## Part IV — Containerization

### [04 · Docker](docs/04-containerization/docker.md)

- Why Docker for ML services
- `Dockerfile` walkthrough — every instruction explained
- `requirements.txt` — pinned dependencies
- Building the image
- Running the container on port 8000
- Verifying the container is healthy
- Useful Docker commands reference

---

## Part V — Server Deployment

### [05 · Deploying on the Linux Server](docs/05-server-deployment/deployment.md)

- Server preparation (Ubuntu 24.04 LTS)
- Installing Docker on the server
- Copying the project to the server (SCP / Git)
- Building and starting the container on the server
- Configuring Docker restart policy
- Verifying the service from inside the server
- Firewall rules (UFW) for port 8000

---

## Part VI — Nginx and HTTPS

### [06 · Nginx Reverse Proxy and HTTPS](docs/06-nginx-https/nginx-setup.md)

- Installing and verifying Nginx
- Writing the server block configuration
- Reverse proxying: `domain → localhost:8000`
- Setting the correct proxy headers
- Enabling HTTPS via Cloudflare (Full SSL mode)
- Alternative: Certbot / Let's Encrypt
- Testing the HTTPS endpoint
- Nginx reload and status commands

---

## Part VII — Observability

### [07 · Logging](docs/07-logging/logging.md)

- What is logged and why
- Python `logging` configuration
- Log format: timestamp, endpoint, input, prediction, latency
- Writing logs to a persistent file inside the container
- Mounting a log volume for host-side access
- Reading and tailing logs in production

---

## Part VIII — Networking

### [08 · Networking Flow](docs/08-networking-flow/networking-flow.md)

- End-to-end request lifecycle
- Layer-by-layer breakdown: Client → Cloudflare → Nginx → Docker → FastAPI → Model
- Port map
- How Nginx and Docker communicate
- TLS termination points
- What happens on each `/predict` call

---

## File Reference

| File | Description |
|---|---|
| `README.md` | Project introduction and quick navigation |
| `INDEX.md` | This file |
| `LICENSE` | MIT License |
| `Dockerfile` | Container definition |
| `app/main.py` | FastAPI application entrypoint |
| `app/model.pkl` | Serialized trained model |
| `app/requirements.txt` | Pinned Python dependency list |
| `docs/01-project-overview/architecture.md` | System architecture |
| `docs/02-base-model/neural-network.md` | Model documentation |
| `docs/03-api-layer/fastapi-service.md` | API documentation |
| `docs/04-containerization/docker.md` | Docker documentation |
| `docs/05-server-deployment/deployment.md` | Server deployment guide |
| `docs/06-nginx-https/nginx-setup.md` | Nginx and HTTPS setup |
| `docs/07-logging/logging.md` | Logging configuration |
| `docs/08-networking-flow/networking-flow.md` | Request lifecycle |
