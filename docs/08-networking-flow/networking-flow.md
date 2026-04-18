# 08 · Networking Flow

*← [Index](../../INDEX.md) · [Logging](../07-logging/logging.md)*

---

## Overview

This document traces a single `/predict` request from the moment a client sends it to the moment the prediction JSON arrives back. Every layer is accounted for.

---

## End-to-End Request Lifecycle

```
Client (browser / curl / Python script)
│
│  POST https://api.yourdomain.com/predict
│  { "pixels": [0.0, 0.12, 0.98, ...] }
│
▼  DNS resolution → Cloudflare IP
┌─────────────────────────────────────────────────┐
│                   Cloudflare                    │
│                                                 │
│  - Receives HTTPS request on port 443           │
│  - TLS termination (client ↔ Cloudflare)        │
│  - DDoS protection check                        │
│  - Forwards to origin server via HTTPS          │
│    (Cloudflare ↔ origin: Full SSL mode)         │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS → server port 443
┌──────────────────────▼──────────────────────────┐
│                Nginx (host)                     │
│                                                 │
│  - Listens on port 443                          │
│  - SSL termination (Cloudflare ↔ Nginx)         │
│  - Matches server_name: api.yourdomain.com      │
│  - Sets proxy headers:                          │
│      X-Real-IP: 203.0.113.42                    │
│      X-Forwarded-For: 203.0.113.42              │
│      X-Forwarded-Proto: https                   │
│  - proxy_pass → http://localhost:8000           │
│  - Writes to access.log                         │
└──────────────────────┬──────────────────────────┘
                       │ HTTP → localhost:8000
┌──────────────────────▼──────────────────────────┐
│          Docker Container (digit-api)           │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │           Uvicorn (ASGI server)         │    │
│  │  - Receives HTTP request on port 8000   │    │
│  │  - Passes to FastAPI application        │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                           │
│  ┌──────────────────▼──────────────────────┐    │
│  │              FastAPI                    │    │
│  │  - Route matched: POST /predict         │    │
│  │  - Pydantic validates request body      │    │
│  │  - 784 floats extracted and checked     │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                           │
│  ┌──────────────────▼──────────────────────┐    │
│  │         NumPy Neural Network            │    │
│  │                                         │    │
│  │  X = pixels.reshape(1, 784)             │    │
│  │  Z1 = X @ W[0] + b[0]  → ReLU          │    │
│  │  Z2 = A1 @ W[1] + b[1] → ReLU          │    │
│  │  Z3 = A2 @ W[2] + b[2] → Softmax       │    │
│  │  predicted = argmax(Z3)                 │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                           │
│  ┌──────────────────▼──────────────────────┐    │
│  │              FastAPI                    │    │
│  │  - Builds PredictResponse               │    │
│  │  - Writes to predictions.log            │    │
│  │  - Returns JSON 200 response            │    │
│  └─────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
                       │
                       │  HTTP 200 response body
                       ▼
                    Nginx
                       │ HTTPS response
                       ▼
                   Cloudflare
                       │ HTTPS response
                       ▼
                    Client
```

---

## Port Map

| Port | Protocol | On | Accessible from |
|---|---|---|---|
| 443 | HTTPS | Nginx (host) | Internet (via Cloudflare) |
| 80 | HTTP | Nginx (host) | Internet → redirected to 443 |
| 8000 | HTTP | Docker container | `localhost` only (UFW blocks external) |

---

## TLS Termination Points

There are two SSL sessions in the Cloudflare Full SSL mode setup:

1. **Client ↔ Cloudflare** — Cloudflare's edge certificate terminates the client's TLS session. The client sees Cloudflare's certificate.

2. **Cloudflare ↔ Nginx** — An origin certificate (issued by Cloudflare) secures the connection between Cloudflare and the server. Nginx presents this certificate.

Communication between Nginx and the Docker container (`localhost:8000`) is plain HTTP. This is secure because it never leaves the server — it travels over the loopback interface, which is not exposed to any network.

---

## What Happens Inside the Neural Network

Each `/predict` call performs one forward pass through the network:

```
Input: 784 floats (normalized pixel values, 0.0–1.0)

Layer 1:
  Z1 = X @ W[0] + b[0]        # (1,784) @ (784,128) + (1,128) = (1,128)
  A1 = ReLU(Z1)                # (1,128)

Layer 2:
  Z2 = A1 @ W[1] + b[1]       # (1,128) @ (128,64) + (1,64) = (1,64)
  A2 = ReLU(Z2)                # (1,64)

Output layer:
  Z3 = A2 @ W[2] + b[2]       # (1,64) @ (64,10) + (1,10) = (1,10)
  Y  = Softmax(Z3)             # (1,10) — probabilities summing to 1.0

Prediction: argmax(Y[0])       # Integer 0–9
```

The model is loaded once at startup and held in memory. Each inference executes three matrix multiplications. For a single sample (batch size 1), NumPy completes this in under 1ms on modern hardware.

---

## Latency Budget

| Step | Typical duration |
|---|---|
| DNS resolution + Cloudflare routing | 10–50ms |
| TLS handshake (first request) | 10–30ms |
| Nginx proxy overhead | < 1ms |
| FastAPI request parsing and validation | < 1ms |
| NumPy forward pass | < 1ms |
| FastAPI response serialization | < 1ms |
| Nginx response forwarding | < 1ms |
| **Total (cold TLS)** | **~20–80ms** |
| **Total (warm, keep-alive)** | **~5–15ms** |

The model inference itself is negligible. Network transit dominates total request latency.

---

## What the Logs Capture

After a request completes, two log entries are written:

**Nginx access log** (`/var/log/nginx/digit-api.access.log`):

```
203.0.113.42 - - [01/Sep/2025:14:23:45 +0530] "POST /predict HTTP/1.1" 200 248 "-" "curl/8.4.0"
```

**Application log** (`/var/log/digit-api/predictions.log`):

```
2025-09-01 14:23:45 | INFO | digit=7 | confidence=0.9843 | latency=1.243ms
```

The Nginx log captures the full HTTP picture. The application log captures what the model decided.

---

*← [07 · Logging](../07-logging/logging.md) | [Index](../../INDEX.md)*
