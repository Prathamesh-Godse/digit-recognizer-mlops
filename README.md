# Digit Recognizer — MLOps Deployment

> **From a NumPy notebook to a publicly accessible ML API — deployed on a hardened Linux server, containerized with Docker, and served over HTTPS via Nginx.**

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Stack](https://img.shields.io/badge/stack-NumPy%20·%20FastAPI%20·%20Docker%20·%20Nginx-blue)
![Platform](https://img.shields.io/badge/platform-Ubuntu%2024.04%20LTS-orange)

---

## What This Project Is

This project takes a handwritten digit recognizer — a fully connected neural network built from scratch using only NumPy — and wraps it into a production-grade ML service. No frameworks. No shortcuts. Every layer of the stack is understood and intentional.

The model learns to classify digits 0–9 from the MNIST dataset using a three-layer MLP:

```
Input (784) → Dense(128, ReLU) → Dense(64, ReLU) → Dense(10, Softmax)
```

It achieves ~97% test accuracy. This project takes that model and makes it usable by anyone over the internet.

---

## Stack

| Layer | Technology | Purpose |
|---|---|---|
| ML Model | NumPy MLP | Digit classification |
| API | FastAPI + Uvicorn | Serve predictions over HTTP |
| Container | Docker | Portable, isolated runtime |
| Server | Ubuntu 24.04 LTS | Production host |
| Reverse Proxy | Nginx | Route traffic, terminate SSL |
| HTTPS | Cloudflare / Let's Encrypt | Encrypted public access |
| Observability | Python `logging` | Prediction audit trail |

---

## Documentation

Full documentation is in the [`docs/`](docs/) folder, organized by stack layer.

**→ [Browse the full documentation index](INDEX.md)**

| Section | Document |
|---|---|
| System architecture | [docs/01-project-overview/architecture.md](docs/01-project-overview/architecture.md) |
| NumPy neural network | [docs/02-base-model/neural-network.md](docs/02-base-model/neural-network.md) |
| FastAPI service | [docs/03-api-layer/fastapi-service.md](docs/03-api-layer/fastapi-service.md) |
| Docker containerization | [docs/04-containerization/docker.md](docs/04-containerization/docker.md) |
| Server deployment | [docs/05-server-deployment/deployment.md](docs/05-server-deployment/deployment.md) |
| Nginx and HTTPS | [docs/06-nginx-https/nginx-setup.md](docs/06-nginx-https/nginx-setup.md) |
| Logging | [docs/07-logging/logging.md](docs/07-logging/logging.md) |
| End-to-end networking flow | [docs/08-networking-flow/networking-flow.md](docs/08-networking-flow/networking-flow.md) |

---

## Repository Structure

```
digit-recognizer-mlops/
│
├── README.md                              ← You are here
├── INDEX.md                               ← Full documentation index
├── LICENSE                                ← MIT
├── Dockerfile                             ← Container definition
│
├── app/
│   ├── main.py                            ← FastAPI application
│   ├── model.pkl                          ← Serialized trained model
│   └── requirements.txt                   ← Pinned Python dependencies
│
└── docs/
    ├── 01-project-overview/
    │   └── architecture.md                ← System design and component map
    ├── 02-base-model/
    │   └── neural-network.md              ← The NumPy model explained
    ├── 03-api-layer/
    │   └── fastapi-service.md             ← FastAPI implementation
    ├── 04-containerization/
    │   └── docker.md                      ← Dockerfile and container workflow
    ├── 05-server-deployment/
    │   └── deployment.md                  ← Deploying and running on Linux server
    ├── 06-nginx-https/
    │   └── nginx-setup.md                 ← Reverse proxy and HTTPS
    ├── 07-logging/
    │   └── logging.md                     ← Prediction logging and latency tracking
    └── 08-networking-flow/
        └── networking-flow.md             ← End-to-end request lifecycle
```

---

## Prerequisites

- Ubuntu 24.04 LTS server (local or cloud)
- Docker installed on the server
- Nginx installed on the server
- A domain name pointed at the server's IP
- Cloudflare account (optional but recommended) or Certbot for SSL

---

## Outcome

By the end of this project:

- A live ML API is reachable at `https://yourdomain.com/predict`
- The model never loads twice — it is cached at startup
- Every prediction is logged with timestamp and latency
- The entire service restarts automatically if the container crashes
- All traffic is encrypted in transit

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Stack: NumPy · FastAPI · Docker · Nginx · Ubuntu 24.04 LTS*
