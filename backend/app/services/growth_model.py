import os
from datetime import datetime, date
from typing import Tuple, Optional

import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
import joblib
from flask import current_app


def _get_models_dir() -> str:
    """Return models directory under Flask instance path."""
    base = current_app.instance_path if current_app else os.path.join(os.getcwd(), 'instance')
    models_dir = os.path.join(base, 'models')
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def get_model_path(ear_num: str) -> str:
    return os.path.join(_get_models_dir(), f"{ear_num}_poly.pkl")


def train_polynomial_model(
    days: np.ndarray,
    weights: np.ndarray,
    degree: int = 2,
    alpha: float = 1.0,
) -> Pipeline:
    """Train a polynomial regression (Ridge) pipeline and return it."""
    model = Pipeline([
        ("poly", PolynomialFeatures(degree=degree, include_bias=False)),
        ("ridge", Ridge(alpha=alpha))
    ])
    model.fit(days.reshape(-1, 1), weights)
    return model


def save_model(ear_num: str, model: Pipeline) -> str:
    path = get_model_path(ear_num)
    try:
        joblib.dump(model, path)
        return path
    except Exception as e:
        raise RuntimeError(f"模型保存失敗: {e}")


def load_model(ear_num: str) -> Optional[Pipeline]:
    path = get_model_path(ear_num)
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        # 損毀或版本不相容
        current_app.logger.warning(f"模型載入失敗({ear_num}): {e}")
        return None


def predict_weight(model: Pipeline, day_from_birth: int) -> float:
    return float(model.predict(np.array([[float(day_from_birth)] ]))[0])


def compute_adg(model: Pipeline, start_day: int, days_forward: int) -> float:
    """Approximate average daily gain over a horizon using finite difference."""
    w_start = predict_weight(model, start_day)
    w_end = predict_weight(model, start_day + days_forward)
    return float((w_end - w_start) / max(days_forward, 1))
