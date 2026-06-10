import json
from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = BASE_DIR / "artifacts"

MODEL_PATH = ARTIFACT_DIR / "AB_LGBM_4_shallow_best.pkl"
FEATURE_COLUMNS_PATH = ARTIFACT_DIR / "feature_columns.json"

model = joblib.load(MODEL_PATH)

feature_columns = list(model.feature_name_)

with open(FEATURE_COLUMNS_PATH, "w") as file:
    json.dump(feature_columns, file, indent=4)

print("Saved feature columns to:", FEATURE_COLUMNS_PATH)
print("Feature count:", len(feature_columns))
print("First 10 features:", feature_columns[:10])