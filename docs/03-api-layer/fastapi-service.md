# 03 · FastAPI Service

*← [Index](../../INDEX.md) · [Neural Network](../02-base-model/neural-network.md)*

---

## Why FastAPI

FastAPI was chosen as the API framework for three concrete reasons:

1. **Automatic input validation.** Request bodies are defined as Pydantic models. If a client sends 783 values instead of 784, or sends strings instead of floats, FastAPI rejects the request with a clear error before the code even runs. No manual validation logic needed.

2. **Interactive documentation at `/docs`.** FastAPI generates a Swagger UI automatically from the code. During development and testing, this is the fastest way to send real requests without writing any client code.

3. **Minimal boilerplate.** A working endpoint is a Python function with a decorator. There is no `app.add_route()`, no request parsing, no manual serialization.

---

## Application Structure

```
app/
├── main.py             ← FastAPI application (this document)
├── model.pkl           ← Trained NeuralNetwork object (pickle)
└── requirements.txt    ← Pinned Python dependencies
```

---

## `requirements.txt`

```
fastapi==0.111.0
uvicorn==0.29.0
numpy==1.26.4
scikit-learn==1.4.2
pydantic==2.7.0
```

All versions are pinned. This ensures that the container built six months from now behaves identically to the container built today.

---

## `main.py` — Full Application

```python
import pickle
import time
import logging
import numpy as np

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List

# ── Logging setup ──────────────────────────────────────────────────────── #
logging.basicConfig(
    filename="predictions.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Load model once at startup ─────────────────────────────────────────── #
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

logger.info("Model loaded successfully at startup")

# ── FastAPI app ────────────────────────────────────────────────────────── #
app = FastAPI(
    title="Digit Recognizer API",
    description="Predicts handwritten digits (0-9) from 28x28 pixel arrays.",
    version="1.0.0",
)

# ── Request schema ─────────────────────────────────────────────────────── #
class PredictRequest(BaseModel):
    pixels: List[float]

    @field_validator("pixels")
    @classmethod
    def validate_pixels(cls, v):
        if len(v) != 784:
            raise ValueError(f"Expected 784 pixel values, got {len(v)}")
        if any(p < 0.0 or p > 1.0 for p in v):
            raise ValueError("Pixel values must be normalized to [0.0, 1.0]")
        return v

# ── Response schema ────────────────────────────────────────────────────── #
class PredictResponse(BaseModel):
    predicted_digit: int
    confidence: float
    probabilities: List[float]
    latency_ms: float

# ── Endpoints ──────────────────────────────────────────────────────────── #
@app.get("/")
def health_check():
    """Returns service status. Used by monitoring and Nginx upstreams."""
    return {"status": "ok", "service": "digit-recognizer", "version": "1.0.0"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Predict the digit in a 28x28 greyscale image.

    - pixels: List of 784 floats, normalized to [0.0, 1.0]
    - Returns: predicted digit, confidence, full probability distribution
    """
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

    return PredictResponse(
        predicted_digit=predicted,
        confidence=round(confidence, 4),
        probabilities=[round(float(p), 4) for p in proba],
        latency_ms=latency_ms,
    )
```

---

## Endpoints Reference

### `GET /`

Health check. Returns immediately with service status. Used to verify the container is running and responsive.

**Response:**
```json
{
  "status": "ok",
  "service": "digit-recognizer",
  "version": "1.0.0"
}
```

---

### `POST /predict`

Accepts a 28×28 image encoded as a flat list of 784 floats normalized to [0.0, 1.0]. Returns the predicted digit and confidence.

**Request body:**
```json
{
  "pixels": [0.0, 0.0, 0.12, 0.98, ...]
}
```

**Successful response (`200 OK`):**
```json
{
  "predicted_digit": 7,
  "confidence": 0.9843,
  "probabilities": [0.0001, 0.0002, 0.0003, 0.0004, 0.0002, 0.0001, 0.0003, 0.9843, 0.0001, 0.0],
  "latency_ms": 1.243
}
```

**Validation error (`422 Unprocessable Entity`):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "msg": "Value error, Expected 784 pixel values, got 500"
    }
  ]
}
```

---

## Running Locally with Uvicorn

From inside the `app/` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- `--host 0.0.0.0` binds to all interfaces (required for Docker)
- `--port 8000` is the standard internal port for this service
- `--reload` enables hot reload during development (remove in production)

---

## Testing via Swagger UI

Once Uvicorn is running, open `http://localhost:8000/docs` in a browser. The auto-generated Swagger UI allows sending real requests interactively — paste a pixel array into the `/predict` form and inspect the response.

---

## Testing via curl

```bash
# Health check
curl http://localhost:8000/

# Predict (example with a zeroed-out 784-element array)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"pixels": ['"$(python3 -c "print(','.join(['0.0']*784))"')"']}'
```

---

## Input Preprocessing Note

The model was trained on MNIST data normalized to [0.0, 1.0] (raw pixel values divided by 255). Clients sending image data must apply the same normalization before calling `/predict`. Raw uint8 values (0–255) will produce incorrect predictions.

---

*→ Next: [04 · Docker](../04-containerization/docker.md)*
