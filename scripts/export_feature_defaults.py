import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = BASE_DIR / "artifacts"

FEATURE_COLUMNS_PATH = ARTIFACT_DIR / "feature_columns.json"
DEFAULTS_PATH = ARTIFACT_DIR / "feature_defaults.json"

# Correct path to your research project
RESEARCH_DATA_DIR = Path(
    r"C:\Users\Sahan\OneDrive\Desktop\sepsis-cdss-research\data\processed"
)

train_a_path = RESEARCH_DATA_DIR / "trainA_testB_train_processed.pkl"
train_b_path = RESEARCH_DATA_DIR / "trainA_testB_test_processed.pkl"

print("Looking for:")
print(train_a_path)
print(train_b_path)

if not train_a_path.exists():
    raise FileNotFoundError(f"Cannot find: {train_a_path}")

if not train_b_path.exists():
    raise FileNotFoundError(f"Cannot find: {train_b_path}")

with open(FEATURE_COLUMNS_PATH, "r") as file:
    feature_columns = json.load(file)

train_a = pd.read_pickle(train_a_path)
train_b = pd.read_pickle(train_b_path)

combined = pd.concat([train_a, train_b], ignore_index=True)

defaults = {}

for feature in feature_columns:
    if feature.endswith("_missing"):
        defaults[feature] = 1.0
    elif feature in combined.columns:
        defaults[feature] = float(combined[feature].median())
    else:
        defaults[feature] = 0.0

with open(DEFAULTS_PATH, "w") as file:
    json.dump(defaults, file, indent=4)

print("Saved:", DEFAULTS_PATH)
print("Feature defaults:", len(defaults))
print("Sample defaults:")
print(dict(list(defaults.items())[:10]))