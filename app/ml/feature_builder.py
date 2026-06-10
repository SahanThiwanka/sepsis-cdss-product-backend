from typing import Dict, Optional, Tuple

import pandas as pd

from app.ml.model_loader import get_feature_columns, get_feature_defaults


def build_feature_dataframe(
    observation: Dict[str, Optional[float]]
) -> Tuple[pd.DataFrame, list[str]]:
    """
    Build one-row feature dataframe in exact model training order.

    Missing numeric features are filled with training median/default values.
    Missing indicator columns are automatically set:
    - 1.0 if the base feature is missing
    - 0.0 if the base feature is present
    """

    feature_columns = get_feature_columns()
    feature_defaults = get_feature_defaults()

    row = {}
    missing_features = []

    for feature in feature_columns:
        if feature.endswith("_missing"):
            base_feature = feature.replace("_missing", "")

            if base_feature in observation and observation[base_feature] is not None:
                row[feature] = 0.0
            else:
                row[feature] = 1.0

            continue

        value = observation.get(feature)

        if value is None:
            row[feature] = float(feature_defaults.get(feature, 0.0))
            missing_features.append(feature)
        else:
            row[feature] = float(value)

    feature_df = pd.DataFrame([row], columns=feature_columns)

    return feature_df, missing_features