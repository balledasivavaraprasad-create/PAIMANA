"""Model loading.

The notebooks pickled custom objects (BaggedHGB, log_shift, inv_log_shift) from
`__main__`, and models 2 and 3 contain xgboost estimators. To load them anywhere
we (a) re-declare the custom classes here and (b) remap `__main__` lookups to
this module while unpickling.
"""
from __future__ import annotations
import logging
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import HistGradientBoostingRegressor

log = logging.getLogger(__name__)
RANDOM_STATE = 42
SHIFT = 100.0


def log_shift(y):
    return np.log1p(np.asarray(y) + SHIFT)


def inv_log_shift(y):
    return np.expm1(y) - SHIFT


class BaggedHGB(BaseEstimator, RegressorMixin):
    """Same definition as notebook 01 (needed only to unpickle the saved model)."""

    def __init__(self, n_models=12, subsample_frac=0.85, max_depth=4, max_leaf_nodes=20,
                 min_samples_leaf=20, l2=1.5, lr=0.035, max_iter=500):
        self.n_models = n_models
        self.subsample_frac = subsample_frac
        self.max_depth = max_depth
        self.max_leaf_nodes = max_leaf_nodes
        self.min_samples_leaf = min_samples_leaf
        self.l2 = l2
        self.lr = lr
        self.max_iter = max_iter

    def fit(self, X, y):  # not used at inference, kept for completeness
        rng = np.random.RandomState(RANDOM_STATE)
        self.models_ = []
        n = len(X)
        for i in range(self.n_models):
            idx = rng.choice(n, size=int(n * self.subsample_frac), replace=True)
            Xi = X.iloc[idx] if hasattr(X, "iloc") else X[idx]
            yi = y.iloc[idx] if hasattr(y, "iloc") else y[idx]
            m = HistGradientBoostingRegressor(
                max_iter=self.max_iter, learning_rate=self.lr, max_depth=self.max_depth,
                max_leaf_nodes=self.max_leaf_nodes, min_samples_leaf=self.min_samples_leaf,
                l2_regularization=self.l2, early_stopping=True, validation_fraction=0.15,
                n_iter_no_change=25, random_state=i)
            m.fit(Xi, yi)
            self.models_.append(m)
        return self

    def predict(self, X):
        return np.column_stack([m.predict(X) for m in self.models_]).mean(axis=1)


_SHIM = {"BaggedHGB": BaggedHGB, "log_shift": log_shift, "inv_log_shift": inv_log_shift}


def load_model(path: str):
    """Load a joblib model, remapping notebook-defined classes."""
    import joblib.numpy_pickle as npp

    class _NPUnpickler(npp.NumpyUnpickler):
        def find_class(self, module, name):
            if module == "__main__" and name in _SHIM:
                return _SHIM[name]
            if module == "_loss":
                try:
                    import sklearn._loss._loss as sll
                    return getattr(sll, name)
                except (ImportError, AttributeError):
                    pass
            return super().find_class(module, name)

    with open(path, "rb") as f:
        return _NPUnpickler(path, f, None).load()
