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
