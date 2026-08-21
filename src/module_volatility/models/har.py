"""
HAR (Heterogeneous Autoregressive) Volatility Models:
1. Standard HAR-RV (Corsi 2009)
2. Cluster-Based HAR (incorporates correlation-cluster volatility spillover)
3. Sector-Based HAR (incorporates sector-specific volatility spillover)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from typing import Dict, Any, Optional, Tuple

class BaseHAR:
    def __init__(self, alpha: float = 0.0):
        self.model = Ridge(alpha=alpha, fit_intercept=True) if alpha > 0 else LinearRegression(fit_intercept=True)
        self.feature_names = []
        self.is_fitted = False

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model is not fitted yet.")
        preds = self.model.predict(X)
        # Realized variance must be strictly non-negative
        return np.maximum(preds, 1e-8)

class StandardHAR(BaseHAR):
    """
    Standard HAR-RV Model:
    RV_{t+1} = beta_0 + beta_d * RV_t^(d) + beta_w * RV_t^(w) + beta_m * RV_t^(m) + epsilon
    """
    def __init__(self):
        super().__init__()
        self.name = "HAR"

    def fit(self, df_features: pd.DataFrame) -> "StandardHAR":
        cols = ["rv_d", "rv_w", "rv_m"]
        X = df_features[cols].values
        y = df_features["target_rv"].values
        self.feature_names = cols
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_df(self, df_features: pd.DataFrame) -> np.ndarray:
        X = df_features[self.feature_names].values
        return self.predict(X)

class ClusterHAR(BaseHAR):
    """
    Cluster-Based HAR Model:
    Augments HAR with the average realized volatility of the asset's correlation cluster.
    RV_{t+1} = beta_0 + beta_d * RV_t^(d) + beta_w * RV_t^(w) + beta_m * RV_t^(m) + beta_c * Cluster_RV_t + epsilon
    """
    def __init__(self):
        super().__init__()
        self.name = "Cluster-HAR"

    def prepare_data(self, df_features: pd.DataFrame, df_cluster_rv: pd.DataFrame) -> pd.DataFrame:
        merged = pd.merge(df_features, df_cluster_rv, on="date", how="left")
        merged["cluster_rv"] = merged["cluster_rv"].fillna(merged["rv_w"])
        return merged

    def fit(self, df_features: pd.DataFrame, df_cluster_rv: pd.DataFrame) -> "ClusterHAR":
        df_prepared = self.prepare_data(df_features, df_cluster_rv)
        cols = ["rv_d", "rv_w", "rv_m", "cluster_rv"]
        X = df_prepared[cols].values
        y = df_prepared["target_rv"].values
        self.feature_names = cols
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_df(self, df_features: pd.DataFrame, df_cluster_rv: pd.DataFrame) -> np.ndarray:
        df_prepared = self.prepare_data(df_features, df_cluster_rv)
        X = df_prepared[self.feature_names].values
        return self.predict(X)

class SectorHAR(BaseHAR):
    """
    Sector-Based HAR Model:
    Augments HAR with the average realized volatility of the asset's industrial sector.
    RV_{t+1} = beta_0 + beta_d * RV_t^(d) + beta_w * RV_t^(w) + beta_m * RV_t^(m) + beta_s * Sector_RV_t + epsilon
    """
    def __init__(self):
        super().__init__()
        self.name = "Sector-HAR"

    def prepare_data(self, df_features: pd.DataFrame, df_sector_rv: pd.DataFrame) -> pd.DataFrame:
        merged = pd.merge(df_features, df_sector_rv, on="date", how="left")
        merged["sector_rv"] = merged["sector_rv"].fillna(merged["rv_w"])
        return merged

    def fit(self, df_features: pd.DataFrame, df_sector_rv: pd.DataFrame) -> "SectorHAR":
        df_prepared = self.prepare_data(df_features, df_sector_rv)
        cols = ["rv_d", "rv_w", "rv_m", "sector_rv"]
        X = df_prepared[cols].values
        y = df_prepared["target_rv"].values
        self.feature_names = cols
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_df(self, df_features: pd.DataFrame, df_sector_rv: pd.DataFrame) -> np.ndarray:
        df_prepared = self.prepare_data(df_features, df_sector_rv)
        X = df_prepared[self.feature_names].values
        return self.predict(X)
