# 02 · The Neural Network

*← [Index](../../INDEX.md) · [Architecture](../01-project-overview/architecture.md)*

---

## What This Is

The model at the center of this project is a three-layer fully connected neural network trained on the MNIST handwritten digit dataset — built entirely from scratch using NumPy. No PyTorch, no TensorFlow, no Keras. Every operation — forward propagation, backpropagation, weight updates — is written explicitly as matrix math.

This document covers the network's architecture, the mathematics behind it, how it was trained, what accuracy it achieves, and how the trained weights are saved and later loaded for inference.

---

## Network Architecture

```
Input (784) → Dense(128, ReLU) → Dense(64, ReLU) → Dense(10, Softmax)
```

Each MNIST image is 28×28 pixels. Flattened, that is 784 floating-point numbers per sample. The network passes this vector through two hidden layers before producing a 10-element probability distribution over digit classes 0–9.

### Weight Dimensions

| Layer | Weight matrix shape | Bias shape | Parameters |
|---|---|---|---|
| Layer 1 | (784, 128) | (1, 128) | 100,480 |
| Layer 2 | (128, 64) | (1, 64) | 8,256 |
| Layer 3 | (64, 10) | (1, 10) | 650 |
| **Total** | | | **109,386** |

---

## Mathematics

### He Weight Initialization

Hidden layers use ReLU activations. ReLU kills negative activations entirely, which means roughly half of each layer's neurons start inactive. Vanilla random initialization (e.g., `N(0,1)`) produces activations that shrink or explode as they pass through many layers.

He initialization corrects for this by scaling the variance to compensate for the dead neurons:

$$W^{[l]} \sim \mathcal{N}\!\left(0,\ \sqrt{\frac{2}{n^{[l-1]}}}\right)$$

In code:

```python
self.W.append(np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in))
self.b.append(np.zeros((1, n_out)))
```

Biases start at zero. This is standard — biases do not need the same variance correction because they are not multiplied by the input.

---

### Forward Propagation

For a batch of N samples, propagation through each layer is:

$$Z^{[l]} = A^{[l-1]} \cdot W^{[l]} + b^{[l]}$$

Hidden layers apply ReLU:

$$A^{[l]} = \max(0,\ Z^{[l]})$$

The output layer applies Softmax with a numerical stability correction (subtracting the row maximum before exponentiation prevents overflow):

$$\text{Softmax}(z_i) = \frac{e^{z_i - \max(z)}}{\sum_j e^{z_j - \max(z)}}$$

---

### Cross-Entropy Loss

The loss function measures how wrong the predictions are. For a batch of N samples, it is the average negative log-probability of the correct class:

$$\mathcal{L} = -\frac{1}{N}\sum_{i=1}^{N} \log(\hat{y}_{i,\, k_i})$$

where $k_i$ is the true class label of sample $i$. A tiny clip (`1e-12`) is applied before the log to prevent `log(0)`.

---

### Backpropagation

Gradients flow backward through the network using the chain rule.

**Output layer** — the Softmax + cross-entropy combination yields a clean closed form:

$$\delta^{[L]} = \hat{Y} - Y_{\text{one-hot}}$$

**Hidden layers** — the error signal is propagated backward through the ReLU derivative:

$$\delta^{[l]} = \left(\delta^{[l+1]} \cdot (W^{[l+1]})^T\right) \odot \text{ReLU}'(Z^{[l]})$$

**Weight and bias gradients:**

$$\frac{\partial \mathcal{L}}{\partial W^{[l]}} = \frac{1}{N}(A^{[l-1]})^T \cdot \delta^{[l]}, \qquad \frac{\partial \mathcal{L}}{\partial b^{[l]}} = \frac{1}{N}\sum_i \delta^{[l]}_i$$

---

### SGD Parameter Update

Parameters are updated using vanilla stochastic gradient descent:

$$W^{[l]} \leftarrow W^{[l]} - \alpha \cdot \frac{\partial \mathcal{L}}{\partial W^{[l]}}$$

$$b^{[l]} \leftarrow b^{[l]} - \alpha \cdot \frac{\partial \mathcal{L}}{\partial b^{[l]}}$$

---

## Training Configuration

| Hyperparameter | Value | Rationale |
|---|---|---|
| Learning rate | 0.1 | Works well with He init and mini-batch SGD |
| Batch size | 128 | Balances gradient noise vs. compute per step |
| Epochs | 30 | Loss converges; no significant overfitting observed |
| Optimizer | Mini-batch SGD | Sufficient for this problem; no momentum needed |
| Train split | 54,000 samples | From the original 60,000 training set |
| Validation split | 6,000 samples | Used to monitor overfitting during training |
| Test set | 10,000 samples | Held out; evaluated once at end |

---

## Training Results

The network achieves approximately **97% accuracy** on the MNIST test set (10,000 samples) after 30 epochs.

| Metric | Value |
|---|---|
| Test accuracy | ~97% |
| Test cross-entropy loss | ~0.10 |
| Baseline (random) | 10.00% |
| State-of-the-art (CNN) | ~99.70% |

The gap between this MLP and SOTA CNNs is expected — convolutional layers exploit the spatial structure of images that a flat MLP ignores.

---

## Saving the Model

After training, the model is serialized to disk using Python's `pickle` module. The entire `NeuralNetwork` object is pickled — this preserves the weight matrices, bias vectors, and training history.

```python
import pickle

# After training
with open("model.pkl", "wb") as f:
    pickle.dump(nn, f)

print("Model saved to model.pkl")
```

The `model.pkl` file is then included in the Docker image at build time (copied into the container via the `Dockerfile`).

---

## Loading the Model for Inference

At API startup, the model is loaded once and held in memory as a module-level variable. This is important — loading `model.pkl` on every request would be ~50–100ms of unnecessary overhead per call.

```python
import pickle
import numpy as np

# Loaded once at module import time
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

def predict_digit(pixels: list[float]) -> dict:
    X = np.array(pixels).reshape(1, 784)
    proba = model.predict_proba(X)[0]          # shape (10,)
    predicted = int(proba.argmax())
    confidence = float(proba[predicted])
    return {
        "predicted_digit": predicted,
        "confidence": round(confidence, 4),
        "probabilities": [round(float(p), 4) for p in proba]
    }
```

---

## What the Model Learned

Visualizing the columns of `W[0]` (reshaped to 28×28) reveals that the first layer neurons develop into edge and stroke detectors — they learn features like vertical strokes, curves, and corner patterns. This happened without any explicit supervision about what "edges" are — purely from minimizing cross-entropy loss on raw pixel data.

This is worth noting because it is the same phenomenon that motivates convolutional neural networks: the useful features for digit recognition are local patterns, and a sufficiently expressive MLP discovers them on its own.

---

*→ Next: [03 · FastAPI Service](../03-api-layer/fastapi-service.md)*
