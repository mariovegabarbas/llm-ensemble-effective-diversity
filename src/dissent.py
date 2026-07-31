"""The dissent measurement apparatus.

The effective number of voices is the Vendi Score (Friedman and Dieng, 2022) and
is **not** reimplemented here: it is computed by the reference implementation,
the ``vendi-score`` package, called through :func:`effective_voices`.

What is original to this study is the per-voice decomposition
:func:`per_model_dissent`, the dissent contribution of each ensemble member.
Note that it does **not** decompose the spectral index: it is a different
functional of the same Gram matrix. Its mean recovers the mean pairwise dissent
of the ensemble, which is n/(n-1) times the internal diversity computed by the
reference implementation over all n^2 entries of the matrix.

Frozen numerical policy, applied wherever the spectrum is used directly:

1. symmetric eigendecomposition;
2. eigenvalues that are negative through rounding are clipped to zero
   (clipped, never taken in absolute value);
3. eigenvalues below a relative tolerance of 1e-12 of the largest are dropped
   from the sum;
4. normalisation by the trace.
"""
import numpy as np
from vendi_score import vendi

EIGENVALUE_RTOL = 1e-12


def similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Gram matrix of L2-normalised embeddings, i.e. cosine similarity.

    The unit diagonal this guarantees is what makes normalising by the trace and
    normalising by n equivalent; an arbitrary kernel does not guarantee it.
    """
    e = np.asarray(embeddings, dtype=float)
    e = e / np.linalg.norm(e, axis=1, keepdims=True)
    return e @ e.T


def _spectrum(matrix: np.ndarray) -> np.ndarray:
    eigenvalues = np.clip(np.linalg.eigvalsh(matrix), 0.0, None)
    if eigenvalues.sum() <= 0.0:
        return np.array([])
    return eigenvalues[eigenvalues >= EIGENVALUE_RTOL * eigenvalues.max()]


def effective_voices(matrix: np.ndarray) -> float:
    """Effective number of distinct voices: the Vendi Score of the matrix.

    Delegates to the reference implementation. The matrix must have a unit
    diagonal, which :func:`similarity_matrix` guarantees.
    """
    return float(vendi.score_K(np.asarray(matrix, dtype=float)))


def normalised_entropy(matrix: np.ndarray) -> float:
    """Von Neumann entropy of the spectrum, normalised to the unit interval.

    A reparameterisation of the same quantity as :func:`effective_voices`, on a
    scale that does not depend on the panel size: ``n_eff = n ** s_norm``. It is
    original to this study, not part of the Vendi Score as published.
    """
    matrix = np.asarray(matrix, dtype=float)
    n = len(matrix)
    if n < 2:
        return 0.0
    eigenvalues = _spectrum(matrix)
    if eigenvalues.size == 0:
        return 0.0
    p = eigenvalues / eigenvalues.sum()
    return float(-np.sum(p * np.log(p)) / np.log(n))


def per_model_dissent(matrix: np.ndarray) -> np.ndarray:
    """Dissent contribution of each voice: 1 - its mean similarity to the rest.

    ``d_i = 1 - (1/(n-1)) * sum_{j != i} M_ij``. The argmax identifies the most
    divergent voice. This is the study's own quantity, and it is a functional of
    the Gram matrix rather than a decomposition of the spectral index.
    """
    matrix = np.asarray(matrix, dtype=float)
    n = len(matrix)
    if n < 2:
        return np.zeros(n)
    off_diagonal_sum = matrix.sum(axis=1) - np.diag(matrix)
    return 1.0 - off_diagonal_sum / (n - 1)


def condition_number(matrix: np.ndarray) -> float:
    """Ratio of largest to smallest eigenvalue; a redundancy diagnostic."""
    eigenvalues = np.clip(np.linalg.eigvalsh(np.asarray(matrix, dtype=float)), 0.0, None)
    smallest = float(eigenvalues.min())
    return float(eigenvalues.max() / smallest) if smallest > 0.0 else float("inf")


def largest_eigenvalue_share(matrix: np.ndarray) -> float:
    """Share of the trace carried by the largest eigenvalue."""
    eigenvalues = _spectrum(matrix)
    return float(eigenvalues.max() / eigenvalues.sum()) if eigenvalues.size else 0.0
