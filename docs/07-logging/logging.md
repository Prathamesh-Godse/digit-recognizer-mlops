# 07 · Logging

*← [Index](../../INDEX.md) · [Nginx and HTTPS](../06-nginx-https/nginx-setup.md)*

---

## Why Logging Matters Here

An ML service without logging is a black box. When a prediction is wrong, or latency spikes, or a client sends malformed input — you need a record. Logging provides an audit trail of every inference the model makes, including what was sent, what was returned, and how long it took.

This project implements two layers of logging:

1. **Application-level logging** — prediction details, latency, and errors written by the FastAPI application itself
2. **Access logging** — HTTP request metadata (IP, method, status code, response size) written by Nginx

---

## Application-Level Logging

### Configuration in `main.py`

The logging module is configured once at the top of `main.py`, before any route handlers:

```python
import logging

logging.basicConfig(
    filename="predictions.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
```

| Parameter | Value | Reason |
|---|---|---|
| `filename` | `predictions.log` | Write to a file, not just stdout |
| `level` | `INFO` | Capture informational messages and above |
| `format` | `timestamp \| level \| message` | Human-readable, easily grep-able |
| `datefmt` | `%Y-%m-%d %H:%M:%S` | Unambiguous ISO-style timestamp |

---

### What Gets Logged

**On startup:**

```
2025-09-01 14:23:01 | INFO | Model loaded successfully at startup
```

**On each successful prediction:**

```
2025-09-01 14:23:45 | INFO | digit=7 | confidence=0.9843 | latency=1.243ms
```

**On inference error:**

```
2025-09-01 14:24:12 | ERROR | Inference error: array reshape failed
```

---

### Logging in the Predict Endpoint

```python
@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    start = time.perf_counter()

    try:
        X = np.array(request.pixels, dtype=np.float32).reshape(1, 784)
        proba = model.predict_proba(X)[0]
        predicted = int(proba.argmax())
        confidence = float(proba[predicted])
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail="Inference failed")

    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    logger.info(
        f"digit={predicted} | confidence={confidence:.4f} | latency={latency_ms}ms"
    )

    return PredictResponse(...)
```

`time.perf_counter()` is used for sub-millisecond accuracy. The latency measurement begins after request parsing and ends just before the response is returned — so it captures inference time plus serialization, but not network time.

---

## Persisting Logs Outside the Container

By default, `predictions.log` lives inside the container's writable layer. If the container is removed, the log is lost.

Mount a host directory as a volume when running the container:

```bash
# Create the log directory on the host
sudo mkdir -p /var/log/digit-api
sudo chown $USER /var/log/digit-api

# Run the container with the volume mount
docker run -d \
  --name digit-api \
  -p 8000:8000 \
  --restart unless-stopped \
  -v /var/log/digit-api:/app \
  digit-api
```

With this setup, `/app/predictions.log` inside the container is physically stored at `/var/log/digit-api/predictions.log` on the host. The log survives container replacements and server reboots.

---

## Reading Logs in Production

```bash
# Read the full log
cat /var/log/digit-api/predictions.log

# Follow live (like tail -f)
tail -f /var/log/digit-api/predictions.log

# Show the last 100 predictions
tail -100 /var/log/digit-api/predictions.log

# Filter for errors only
grep "ERROR" /var/log/digit-api/predictions.log

# Count predictions by digit class
grep "digit=" /var/log/digit-api/predictions.log | \
  grep -oP 'digit=\K[0-9]+' | \
  sort | uniq -c | sort -rn

# Show high-latency predictions (above 10ms)
awk -F'latency=' '$2 > 10' /var/log/digit-api/predictions.log
```

---

## Nginx Access Log

Nginx writes its own access log at `/var/log/nginx/digit-api.access.log`. This captures HTTP-level metadata for every request — before it even reaches FastAPI.

Sample access log entry:

```
203.0.113.42 - - [01/Sep/2025:14:23:45 +0530] "POST /predict HTTP/1.1" 200 248 "-" "curl/8.4.0"
```

Fields: client IP, date/time, HTTP method, path, protocol, status code, response size (bytes), referrer, user agent.

Tail the Nginx access log:

```bash
sudo tail -f /var/log/nginx/digit-api.access.log
```

The Nginx log shows the raw HTTP picture (including rejected requests, 404s, timeouts). The application log shows the ML picture (predictions, confidences, latency). Both are needed.

---

## Log Rotation

Left unmanaged, `predictions.log` grows indefinitely. Configure `logrotate` to rotate it automatically:

```bash
sudo nano /etc/logrotate.d/digit-api
```

```
/var/log/digit-api/predictions.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

This keeps 30 days of compressed daily logs. Test it:

```bash
sudo logrotate -d /etc/logrotate.d/digit-api
```

---

## Summary

| Log source | Location | What it captures |
|---|---|---|
| FastAPI application | `/var/log/digit-api/predictions.log` | Digit predicted, confidence, latency, errors |
| Nginx access log | `/var/log/nginx/digit-api.access.log` | HTTP method, status, client IP, response size |
| Nginx error log | `/var/log/nginx/digit-api.error.log` | Proxy errors, SSL issues, timeouts |
| Docker logs | `docker logs digit-api` | Uvicorn stdout, startup messages |

---

*→ Next: [08 · Networking Flow](../08-networking-flow/networking-flow.md)*
