"""
PCA-HAR-Backfill Volatility Model:
Applies Principal Component Analysis (PCA) on multi-scale volatility features to extract
systematic variance factors and backfill missing/noisy history before HAR fitting.
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from typing import Dict, Any, Optional, List, Tuple

class PCAHARBackfillModel:
    """
    PCA-HAR-Backfill Model:
    1. Extracts latent orthogonal principal components from cross-lag features.
    2. Uses inverse PCA projection to reconstruct / backfill missing and noisy history.
    3. Regresses next-day realized variance on principal component representations.
    """
    def __init__(self, n_components: int = 3, alpha: float = 0.01):
        self.name = "PCA-HAR-Backfill"
        self.n_components = n_components
        self.alpha = alpha
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.regressor = Ridge(alpha=alpha, fit_intercept=True)
        self.feature_cols = ["rv_d", "rv_w", "rv_m", "bv_d", "ret_d"]
        self.is_fitted = False

    def backfill_features(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """
        Backfill missing values in historical feature series using PCA reconstruction.
        """
        df = df_features.copy()
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = df.get("rv_d", 0.0)

        X = df[self.feature_cols].copy()
        
        # Initial fill for missing values using rolling / median
        X_imputed = X.ffill().bfill().fillna(0.0).values
        
        if len(X_imputed) > self.n_components:
            scaler_temp = StandardScaler()
            X_scaled = scaler_temp.fit_transform(X_imputed)
            
            k = min(self.n_components, X_scaled.shape[1], X_scaled.shape[0] - 1)
            pca_temp = PCA(n_components=k)
            scores = pca_temp.fit_transform(X_scaled)
            X_reconstructed_scaled = pca_temp.inverse_transform(scores)
            X_reconstructed = scaler_temp.inverse_transform(X_reconstructed_scaled)
            
            # Where original was NaN or <= 0, backfill from reconstructed
            for i, col in enumerate(self.feature_cols):
                orig_vals = df[col].values.copy()
                mask = np.isnan(orig_vals) | (orig_vals <= 0)
                orig_vals[mask] = np.maximum(X_reconstructed[mask, i], 1e-8)
                df[col] = orig_vals
                
        return df

    def fit(self, df_features: pd.DataFrame) -> "PCAHARBackfillModel":
        df_clean = self.backfill_features(df_features)
        
        # Available feature columns
        available_cols = [c for c in self.feature_cols if c in df_clean.columns]
        X = df_clean[available_cols].values
        y = df_clean["target_rv"].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Determine valid number of PCA components
        n_comp = min(self.n_components, X.shape[1], X.shape[0] - 1)
        self.pca = PCA(n_components=n_comp)
        
        # Transform to principal component factor space
        Z = self.pca.fit_transform(X_scaled)
        
        # Fit regression on PCA latent factors
        self.regressor.fit(Z, y)
        self.is_fitted = True
        return self

    def predict_df(self, df_features: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("PCAHARBackfillModel must be fitted before predict.")
            
        df_clean = self.backfill_features(df_features)
        available_cols = [c for c in self.feature_cols if c in df_clean.columns]
        X = df_clean[available_cols].values
        
        X_scaled = self.scaler.transform(X)
        Z = self.pca.transform(X_scaled)
        preds = self.regressor.predict(Z)
        return np.maximum(preds, 1e-8)
