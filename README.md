# Digit Recognizer — MLOps Deployment

> **From a NumPy notebook to a publicly accessible ML API — deployed on a hardened Linux server, containerized with Docker, and served over HTTPS via Nginx.**

---

## What This Project Is

This project takes a handwritten digit recognizer — a fully connected neural network built from scratch using only NumPy — and wraps it into a production-grade ML service. No frameworks. No shortcuts. Every layer of the stack is understood and intentional.

The model learns to classify digits 0–9 from the MNIST dataset using a three-layer MLP:

```
Input (784) → Dense(128, ReLU) → Dense(64, ReLU) → Dense(10, Softmax)
```

It achieves ~97% test accuracy. This project takes that model and makes it usable by anyone over the internet.

---

## What Gets Built

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

## Repository Structure

```
digit-recognizer-mlops/
│
├── README.md                        ← You are here
├── INDEX.md                         ← Full table of contents
│
├── docs/
│   ├── 01-project-overview/
│   │   └── architecture.md          ← System design and component map
│   │
│   ├── 02-base-model/
│   │   └── neural-network.md        ← The NumPy model explained
│   │
│   ├── 03-api-layer/
│   │   └── fastapi-service.md       ← FastAPI implementation
│   │
│   ├── 04-containerization/
│   │   └── docker.md                ← Dockerfile and container workflow
│   │
│   ├── 05-server-deployment/
│   │   └── deployment.md            ← Copying and running on Linux server
│   │
│   ├── 06-nginx-https/
│   │   └── nginx-setup.md           ← Reverse proxy and HTTPS
│   │
│   ├── 07-logging/
│   │   └── logging.md               ← Prediction logging and latency tracking
│   │
│   └── 08-networking-flow/
│       └── networking-flow.md       ← End-to-end request lifecycle
│
├── app/
│   ├── main.py                      ← FastAPI application
│   ├── model.pkl                    ← Serialized trained model
│   └── requirements.txt             ← Python dependencies
│
└── Dockerfile                       ← Container definition
```

---

## Quick Reference

| Goal | Where to look |
|---|---|
| Understand the full system | `docs/01-project-overview/architecture.md` |
| Re-train and export the model | `docs/02-base-model/neural-network.md` |
| Run the API locally | `docs/03-api-layer/fastapi-service.md` |
| Build and run the Docker container | `docs/04-containerization/docker.md` |
| Deploy on the server | `docs/05-server-deployment/deployment.md` |
| Set up Nginx + HTTPS | `docs/06-nginx-https/nginx-setup.md` |
| Understand logging | `docs/07-logging/logging.md` |
| Trace a request end-to-end | `docs/08-networking-flow/networking-flow.md` |

---

## Prerequisites

- Ubuntu 24.04 LTS server (local or cloud)
- Docker installed on the server
- Nginx installed on the server
- A domain name pointed at your server's IP
- Cloudflare account (optional but recommended) or Certbot for SSL

---

## Outcome

By the end of this project:

- A live ML API is reachable at `https://yourdomain.com/predict`
- The model never loads twice — it's cached at startup
- Every prediction is logged with timestamp and latency
- The entire service restarts automatically if the container crashes
- All traffic is encrypted in transit

---

*Built on top of: [neural_network_from_scratch.ipynb](neural_network_from_scratch.ipynb)*
*Stack: NumPy · FastAPI · Docker · Nginx · Ubuntu 24.04 LTS*
