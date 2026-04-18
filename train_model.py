"""
train_model.py
──────────────
Trains a three-layer fully connected neural network on MNIST using NumPy
(no PyTorch, no TensorFlow). Saves the trained model to app/model.pkl.

Architecture:
    Input (784) → Dense(128, ReLU) → Dense(64, ReLU) → Dense(10, Softmax)

Usage:
    pip install numpy scikit-learn
    python train_model.py

Output:
    app/model.pkl  ← ready for the FastAPI service
"""

import pickle
import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split


# ── Neural Network ─────────────────────────────────────────────────────── #

class NeuralNetwork:
    """
    Three-layer MLP trained with mini-batch SGD.

    Layers : [784] → Dense(128, ReLU) → Dense(64, ReLU) → Dense(10, Softmax)
    Loss   : Cross-entropy
    Init   : He initialization for hidden layers, zeros for biases
    """

    def __init__(self, layer_dims: list, learning_rate: float = 0.1):
        self.lr = learning_rate
        self.W = []
        self.b = []
        self.loss_history = []

        # He initialization
        for i in range(len(layer_dims) - 1):
            n_in  = layer_dims[i]
            n_out = layer_dims[i + 1]
            self.W.append(np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in))
            self.b.append(np.zeros((1, n_out)))

    # ── Activations ──────────────────────────────────────────────────── #

    @staticmethod
    def _relu(Z):
        return np.maximum(0, Z)

    @staticmethod
    def _relu_deriv(Z):
        return (Z > 0).astype(float)

    @staticmethod
    def _softmax(Z):
        # Subtract row-max for numerical stability
        Z_shifted = Z - Z.max(axis=1, keepdims=True)
        exp_Z = np.exp(Z_shifted)
        return exp_Z / exp_Z.sum(axis=1, keepdims=True)

    # ── Forward pass ─────────────────────────────────────────────────── #

    def _forward(self, X):
        """Returns list of (Z, A) tuples for each layer."""
        cache = []
        A = X
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            Z = A @ W + b
            if i < len(self.W) - 1:
                A = self._relu(Z)
            else:
                A = self._softmax(Z)   # output layer
            cache.append((Z, A))
        return cache

    # ── Loss ─────────────────────────────────────────────────────────── #

    @staticmethod
    def _cross_entropy(Y_hat, Y_onehot):
        N = Y_onehot.shape[0]
        log_probs = np.log(Y_hat + 1e-12)
        return -np.sum(Y_onehot * log_probs) / N

    # ── Backward pass ────────────────────────────────────────────────── #

    def _backward(self, X, Y_onehot, cache):
        N = X.shape[0]
        grads_W = []
        grads_b = []

        # Output layer gradient (softmax + cross-entropy closed form)
        delta = cache[-1][1] - Y_onehot    # shape (N, 10)

        for i in reversed(range(len(self.W))):
            A_prev = cache[i - 1][1] if i > 0 else X
            dW = A_prev.T @ delta / N
            db = delta.mean(axis=0, keepdims=True)
            grads_W.insert(0, dW)
            grads_b.insert(0, db)

            if i > 0:
                delta = (delta @ self.W[i].T) * self._relu_deriv(cache[i - 1][0])

        return grads_W, grads_b

    # ── Parameter update ─────────────────────────────────────────────── #

    def _update(self, grads_W, grads_b):
        for i in range(len(self.W)):
            self.W[i] -= self.lr * grads_W[i]
            self.b[i] -= self.lr * grads_b[i]

    # ── Training ─────────────────────────────────────────────────────── #

    def fit(self, X_train, y_train, X_val, y_val,
            epochs: int = 30, batch_size: int = 128):
        n_classes = self.W[-1].shape[1]
        N = X_train.shape[0]

        for epoch in range(1, epochs + 1):
            # Shuffle
            idx = np.random.permutation(N)
            X_shuf, y_shuf = X_train[idx], y_train[idx]

            # Mini-batch SGD
            for start in range(0, N, batch_size):
                X_batch = X_shuf[start:start + batch_size]
                y_batch = y_shuf[start:start + batch_size]
                Y_onehot = np.eye(n_classes)[y_batch]

                cache = self._forward(X_batch)
                grads_W, grads_b = self._backward(X_batch, Y_onehot, cache)
                self._update(grads_W, grads_b)

            # Epoch metrics
            train_proba = self.predict_proba(X_train)
            train_loss  = self._cross_entropy(train_proba, np.eye(n_classes)[y_train])
            train_acc   = (train_proba.argmax(axis=1) == y_train).mean()

            val_proba = self.predict_proba(X_val)
            val_loss  = self._cross_entropy(val_proba, np.eye(n_classes)[y_val])
            val_acc   = (val_proba.argmax(axis=1) == y_val).mean()

            self.loss_history.append(train_loss)

            print(
                f"Epoch {epoch:02d}/{epochs} | "
                f"train_loss={train_loss:.4f}  train_acc={train_acc:.4f} | "
                f"val_loss={val_loss:.4f}  val_acc={val_acc:.4f}"
            )

    # ── Inference ────────────────────────────────────────────────────── #

    def predict_proba(self, X) -> np.ndarray:
        """Returns softmax probability distribution, shape (N, 10)."""
        cache = self._forward(X)
        return cache[-1][1]

    def predict(self, X) -> np.ndarray:
        """Returns predicted class indices, shape (N,)."""
        return self.predict_proba(X).argmax(axis=1)


# ── Main ───────────────────────────────────────────────────────────────── #

def main():
    print("Loading MNIST dataset...")
    mnist = fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
    X = mnist.data.astype(np.float32) / 255.0   # normalize to [0.0, 1.0]
    y = mnist.target.astype(int)

    # Split: 54k train / 6k val / 10k test (as documented)
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=10_000, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=6_000, random_state=42, stratify=y_trainval
    )

    print(f"Train: {X_train.shape[0]} | Val: {X_val.shape[0]} | Test: {X_test.shape[0]}")

    # Build and train
    np.random.seed(42)
    nn = NeuralNetwork(
        layer_dims=[784, 128, 64, 10],
        learning_rate=0.1,
    )

    print("\nTraining...\n")
    nn.fit(X_train, y_train, X_val, y_val, epochs=30, batch_size=128)

    # Evaluate on held-out test set
    test_proba = nn.predict_proba(X_test)
    test_acc   = (test_proba.argmax(axis=1) == y_test).mean()
    print(f"\nTest accuracy: {test_acc:.4f}")

    # Save
    output_path = "app/model.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(nn, f)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    main()
