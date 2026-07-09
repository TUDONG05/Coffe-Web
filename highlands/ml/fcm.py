"""
Fuzzy C-Means (FCM) clustering - standalone implementation.
Adapted from /NCKH/c_means/fcm_np.py, self-contained (no external project deps).
"""

import numpy as np
import time
from scipy.spatial.distance import cdist


def _division_by_zero(data: np.ndarray) -> np.ndarray:
    data = data.copy()
    data[data == 0] = np.finfo(float).eps
    return data


def extract_labels(membership: np.ndarray) -> np.ndarray:
    """Defuzzify: assign each point to the cluster with highest membership."""
    return np.argmax(membership, axis=1)


class FCM:
    """
    Fuzzy C-Means clustering.

    Parameters
    ----------
    X          : array-like, shape (n_samples, n_features)
    n_clusters : number of clusters
    m          : fuzziness exponent (>1, typically 2)
    max_iter   : maximum iterations
    epsilon    : convergence tolerance
    seed       : random seed for reproducibility
    """

    def __init__(
        self,
        X: np.ndarray,
        n_clusters: int = 4,
        m: float = 2.0,
        max_iter: int = 300,
        epsilon: float = 1e-5,
        seed: int = 42,
    ):
        self.X = np.array(X, dtype=np.float64)
        self.n_clusters = n_clusters
        self.m = m
        self.max_iter = max_iter
        self.epsilon = epsilon
        self.seed = seed

        self.n_data, self.n_features = self.X.shape
        self.u = self._init_membership()
        self.centroids = self._update_centroids()

        self.elapsed = 0.0
        self.n_iter = 0
        self.history_J: list[float] = []

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_membership(self) -> np.ndarray:
        """Random membership matrix, rows sum to 1."""
        np.random.seed(self.seed)
        u = np.random.rand(self.n_data, self.n_clusters)
        return u / u.sum(axis=1, keepdims=True)

    # ------------------------------------------------------------------
    # Core FCM steps
    # ------------------------------------------------------------------

    def _update_centroids(self) -> np.ndarray:
        """Weighted centroids: V_j = sum(u_ij^m * x_i) / sum(u_ij^m)."""
        um = self.u ** self.m          # (n_data, n_clusters)
        return (um.T @ self.X) / um.sum(axis=0, keepdims=True).T

    def _update_membership(self) -> np.ndarray:
        """Update membership matrix U via FCM formula."""
        d = _division_by_zero(cdist(self.X, self.centroids))   # (n, c)
        # ratio d_ij / d_ik for all k: shape (n, c, c)
        ratio = (d[:, :, None] / d[:, None, :]) ** (2.0 / (self.m - 1))
        u = 1.0 / ratio.sum(axis=2)
        return u / u.sum(axis=1, keepdims=True)

    def _objective(self) -> float:
        """Fuzzy objective function J_m."""
        d = _division_by_zero(cdist(self.X, self.centroids))
        return float(np.sum((self.u ** self.m) * d ** 2))

    def _converged(self, old_u: np.ndarray) -> bool:
        return float(np.linalg.norm(self.u - old_u)) < self.epsilon

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self):
        """Run FCM until convergence or max_iter.

        Returns
        -------
        u          : membership matrix (n_data, n_clusters)
        centroids  : cluster centres (n_clusters, n_features)
        n_iter     : iterations performed
        """
        t0 = time.time()
        for i in range(self.max_iter):
            self.n_iter += 1
            old_u = self.u.copy()
            self.centroids = self._update_centroids()
            self.u = self._update_membership()
            self.history_J.append(self._objective())
            if self._converged(old_u):
                break
        self.elapsed = time.time() - t0
        return self.u, self.centroids, self.n_iter

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        """Compute membership degrees for new samples.

        Returns
        -------
        u : membership matrix (n_samples, n_clusters)
        """
        X_new = np.array(X_new, dtype=np.float64)
        d = np.linalg.norm(X_new[:, None, :] - self.centroids[None, :, :], axis=2)
        d = np.where(d == 0, np.finfo(float).eps, d)
        ratio = (d[:, :, None] / d[:, None, :]) ** (2.0 / (self.m - 1))
        u = 1.0 / ratio.sum(axis=2)
        return u / u.sum(axis=1, keepdims=True)
