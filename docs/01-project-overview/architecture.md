# 01 · Project Architecture

*← [Index](../../INDEX.md)*

---

## Overview

This project is organized as a layered stack where each layer has a single, clear responsibility. The neural network sits at the bottom; every layer above it exists to make that model accessible, reliable, and observable.

```
┌────────────────────────────────────────┐
│           Internet / Client            │
└──────────────────┬─────────────────────┘
                   │ HTTPS (443)
┌──────────────────▼─────────────────────┐
│            Cloudflare / SSL            │
│         (TLS termination layer)        │
└──────────────────┬─────────────────────┘
                   │ HTTP (proxied)
┌──────────────────▼─────────────────────┐
│              Nginx Server              │
│     Reverse proxy on port 80/443       │
└──────────────────┬─────────────────────┘
                   │ HTTP → localhost:8000
┌──────────────────▼─────────────────────┐
│          Docker Container              │
│   ┌─────────────────────────────────┐  │
│   │         FastAPI + Uvicorn       │  │
│   │         (port 8000 inside)      │  │
│   │                                 │  │
│   │   ┌─────────────────────────┐   │  │
│   │   │   NumPy Neural Network  │   │  │
│   │   │     (model.pkl)         │   │  │
│   │   └─────────────────────────┘   │  │
│   └─────────────────────────────────┘  │
└────────────────────────────────────────┘
           Ubuntu 24.04 LTS Server
```

---

## Component Responsibilities

### NumPy Neural Network (the model)
The core of the system. A three-layer fully connected network trained on MNIST. It takes a 784-element float array (a 28×28 greyscale image flattened) and returns a predicted digit (0–9) along with a probability distribution over all 10 classes.

The trained weights are serialized using Python's `pickle` module and stored as `model.pkl`. At API startup, this file is loaded once and kept in memory for the lifetime of the process.

### FastAPI + Uvicorn (the API layer)
FastAPI provides the HTTP interface. Uvicorn is the ASGI server that runs it. Together, they handle incoming HTTP requests, validate the input, pass pixel data to the model, and return a structured JSON response.

FastAPI was chosen over Flask because it provides automatic request validation (via Pydantic), auto-generated interactive docs at `/docs`, and native async support — all with minimal boilerplate.

### Docker (the container)
The FastAPI application and all its Python dependencies run inside a Docker container. This ensures that the runtime environment is identical everywhere — on a local machine and on the production server. The container exposes port 8000 to the host.

### Nginx (the reverse proxy)
Nginx runs on the host server and listens on ports 80 and 443. It forwards all incoming requests to `localhost:8000` where Docker is listening. Nginx also handles SSL termination (when using Let's Encrypt directly) and sets the correct proxy headers so the FastAPI app sees the real client IP.

### Cloudflare (DNS + SSL)
Cloudflare sits in front of the server and provides DNS resolution, DDoS protection, and SSL offloading. In Full SSL mode, traffic between the client and Cloudflare is encrypted, and traffic between Cloudflare and Nginx is also encrypted via an origin certificate. This is the same setup used in the WordPress server project.

---

## Port Map

| Port | Protocol | Listener | Purpose |
|---|---|---|---|
| 443 | HTTPS | Cloudflare / Nginx | Public-facing encrypted traffic |
| 80 | HTTP | Nginx | Redirect to 443 |
| 8000 | HTTP | Docker (Uvicorn) | Internal API port |

Port 8000 is **not** exposed to the public. UFW blocks it from external access. Only Nginx on localhost can reach it.

---

## Technology Choices

| Choice | Alternative | Reason chosen |
|---|---|---|
| FastAPI | Flask | Auto validation, async, /docs built-in |
| Uvicorn | Gunicorn | Native ASGI, fits FastAPI's async model |
| Docker | venv only | Reproducible runtime, easy to move |
| Nginx | Apache | Same server already configured for WordPress |
| Cloudflare SSL | Certbot alone | Integrates with existing domain setup |
| pickle | ONNX, joblib | Simplest path for a pure NumPy model |

---

## Data Flow Summary

A single `/predict` call travels this path:

1. Client sends a POST request with pixel data to `https://yourdomain.com/predict`
2. Cloudflare receives the HTTPS request, decrypts it, and forwards to the server's port 443
3. Nginx receives the request and proxies it to `localhost:8000`
4. Docker exposes port 8000 to localhost; Uvicorn receives the request
5. FastAPI validates the request body (784 floats, values 0.0–1.0)
6. The neural network runs forward propagation on the input
7. The predicted digit and confidence scores are returned as JSON
8. Latency and prediction are written to the log file
9. The response travels back up the same path to the client

---

*→ Next: [02 · The Neural Network](../02-base-model/neural-network.md)*
