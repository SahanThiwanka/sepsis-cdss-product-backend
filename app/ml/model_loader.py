import json
from pathlib import Path
from functools import lru_cache

import joblib


BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACT_DIR / "AB_LGBM_4_shallow_best.pkl"
CALIBRATOR_PATH = ARTIFACT_DIR / "ab_lightgbm_isotonic_calibrator.pkl"
CONFIG_PATH = ARTIFACT_DIR / "model_config.json"
FEATURE_COLUMNS_PATH = ARTIFACT_DIR / "feature_columns.json"
FEATURE_DEFAULTS_PATH = ARTIFACT_DIR / "feature_defaults.json"


@lru_cache
def get_model_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Model config not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r") as file:
        return json.load(file)


@lru_cache
def get_feature_columns():
    if not FEATURE_COLUMNS_PATH.exists():
        raise FileNotFoundError(f"Feature columns not found: {FEATURE_COLUMNS_PATH}")

    with open(FEATURE_COLUMNS_PATH, "r") as file:
        return json.load(file)


@lru_cache
def load_lightgbm_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    return joblib.load(MODEL_PATH)


@lru_cache
def load_calibrator():
    if not CALIBRATOR_PATH.exists():
        raise FileNotFoundError(f"Calibrator file not found: {CALIBRATOR_PATH}")

    return joblib.load(CALIBRATOR_PATH)

@lru_cache
def get_feature_defaults():
    if not FEATURE_DEFAULTS_PATH.exists():
        raise FileNotFoundError(f"Feature defaults not found: {FEATURE_DEFAULTS_PATH}")

    with open(FEATURE_DEFAULTS_PATH, "r") as file:
        return json.load(file)
    
