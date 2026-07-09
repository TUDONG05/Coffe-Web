"""
K-Means clustering - standalone implementation.
Adapted from /NCKH/k_means/km.py, self-contained (no external project deps).
"""

import time
import numpy as np


class KMeans:
    """
    K-Means clustering.

    Parameters
    ----------
    X          : array-like, shape (n_samples, n_features)
    n_clusters : number of clusters
    max_iter   : maximum iterations
    epsilon    : convergence tolerance
    seed       : random seed
    """

    def __init__(
        self,
        X: np.ndarray,
        n_clusters: int = 4,
        max_iter: int = 300,
        epsilon: float = 1e-5,
        seed: int = 42,
    ):
        self.X = np.array(X, dtype=np.float64)
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.epsilon = epsilon
        self.seed = seed

        self.n_data, self.n_features = self.X.shape
        self.centroids = self._init_centroids()
        self.labels = np.zeros(self.n_data, dtype=int)

        self.elapsed = 0.0
        self.n_iter = 0

    def _init_centroids(self) -> np.ndarray:
        """Chọn ngẫu nhiên n_clusters điểm làm tâm cụm ban đầu."""
        np.random.seed(self.seed)
        idx = np.random.choice(self.n_data, self.n_clusters, replace=False)
        return self.X[idx].copy()

    def _update_labels(self) -> np.ndarray:
        """Gán mỗi điểm vào cụm có tâm gần nhất."""
        d = np.linalg.norm(self.X[:, np.newaxis] - self.centroids, axis=2)  # (n, k)
        return np.argmin(d, axis=1)

    def _update_centroids(self) -> np.ndarray:
        """Cập nhật tâm cụm = trung bình các điểm thuộc cụm."""
        new_c = np.zeros_like(self.centroids)
        for i in range(self.n_clusters):
            members = self.X[self.labels == i]
            new_c[i] = members.mean(axis=0) if len(members) > 0 else self.centroids[i]
        return new_c

    def _converged(self, old_centroids: np.ndarray) -> bool:
        return float(np.linalg.norm(self.centroids - old_centroids)) < self.epsilon

    def fit(self):
        """Run K-Means until convergence or max_iter.

        Returns
        -------
        labels    : cluster assignment per sample (n_data,)
        centroids : cluster centres (n_clusters, n_features)
        n_iter    : iterations performed
        """
        t0 = time.time()
        for i in range(self.max_iter):
            self.n_iter += 1
            old_centroids = self.centroids.copy()
            self.labels = self._update_labels()
            self.centroids = self._update_centroids()
            if self._converged(old_centroids):
                break
        self.elapsed = time.time() - t0
        return self.labels, self.centroids, self.n_iter
