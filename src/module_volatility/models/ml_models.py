"""
Machine Learning Volatility Models: LightGBM and XGBoost Regressors.
Captures non-linear autoregressive dependencies and leverage effects in Realized Variance.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
import lightgbm as lgb
import xgboost as xgb

class LightGBMVolModel:
    """
    LightGBM Gradient Boosting Model for Realized Volatility Forecasting.
    """
    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.03,
        max_depth: int = 4,
        num_leaves: int = 15,
        random_state: int = 42
    ):
        self.name = "LightGBM"
        self.model = lgb.LGBMRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            num_leaves=num_leaves,
            random_state=random_state,
            verbosity=-1
        )
        self.feature_names = ["rv_d", "rv_w", "rv_m", "bv_d", "jump_d", "jump_ratio", "ret_d"]
        self.is_fitted = False

    def fit(self, df_features: pd.DataFrame) -> "LightGBMVolModel":
        cols = [c for c in self.feature_names if c in df_features.columns]
        self.feature_names = cols
        X = df_features[cols].values
        y = df_features["target_rv"].values
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_df(self, df_features: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("LightGBMVolModel must be fitted before predict.")
        X = df_features[self.feature_names].values
        preds = self.model.predict(X)
        return np.maximum(preds, 1e-8)

class XGBoostVolModel:
    """
    XGBoost Regressor for Realized Volatility Forecasting.
    """
    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.03,
        max_depth: int = 3,
        random_state: int = 42
    ):
        self.name = "XGBoost"
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            objective="reg:squarederror",
            verbosity=0
        )
        self.feature_names = ["rv_d", "rv_w", "rv_m", "bv_d", "jump_d", "jump_ratio", "ret_d"]
        self.is_fitted = False

    def fit(self, df_features: pd.DataFrame) -> "XGBoostVolModel":
        cols = [c for c in self.feature_names if c in df_features.columns]
        self.feature_names = cols
        X = df_features[cols].values
        y = df_features["target_rv"].values
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_df(self, df_features: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("XGBoostVolModel must be fitted before predict.")
        X = df_features[self.feature_names].values
        preds = self.model.predict(X)
        return np.maximum(preds, 1e-8)
