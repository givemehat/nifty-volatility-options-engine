"""
Statistical evaluation metrics for Volatility Forecasting and Diebold-Mariano tests.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Tuple, Literal

def r2_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute R-squared (Coefficient of Determination) for volatility forecasts.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1.0 - (ss_res / ss_tot))

def qlike_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute the Quasi-Likelihood (QLIKE) robust loss function:
    QLIKE(y, y_hat) = y / y_hat - log(y / y_hat) - 1
    Used as the standard asymmetric loss function in volatility literature (Patton 2011).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    # Clip to avoid log(0) or division by zero
    eps = 1e-8
    y_true_clipped = np.maximum(y_true, eps)
    y_pred_clipped = np.maximum(y_pred, eps)
    
    ratio = y_true_clipped / y_pred_clipped
    loss = ratio - np.log(ratio) - 1.0
    return float(np.mean(loss))

def rmse_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Root Mean Squared Error.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def mae_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Mean Absolute Error.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))

def diebold_mariano_test(
    y_true: np.ndarray,
    y_pred1: np.ndarray,
    y_pred2: np.ndarray,
    loss_type: Literal["qlike", "mse", "mae"] = "qlike",
    h: int = 1,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform the Diebold-Mariano (DM) test for comparing two volatility forecasting models.
    
    Null Hypothesis H0: E[d_t] = 0 (both models have equal predictive accuracy).
    Alternative H1: E[d_t] != 0 (one model significantly outperforms the other).
    
    Parameters:
        y_true: Actual realized variance / volatility array.
        y_pred1: Forecasts from Model 1.
        y_pred2: Forecasts from Model 2.
        loss_type: 'qlike', 'mse', or 'mae'.
        h: Forecast horizon (default 1 for 1-step ahead).
        alpha: Significance level (default 0.05).
        
    Returns:
        Dict with dm_stat, p_value, is_significant, better_model.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred1 = np.asarray(y_pred1, dtype=float)
    y_pred2 = np.asarray(y_pred2, dtype=float)
    
    T = len(y_true)
    if T < 5:
        return {
            "dm_stat": 0.0,
            "p_value": 1.0,
            "is_significant": False,
            "better_model": "insufficient_data"
        }
        
    eps = 1e-8
    if loss_type == "qlike":
        y1_c = np.maximum(y_pred1, eps)
        y2_c = np.maximum(y_pred2, eps)
        yt_c = np.maximum(y_true, eps)
        
        loss1 = (yt_c / y1_c) - np.log(yt_c / y1_c) - 1.0
        loss2 = (yt_c / y2_c) - np.log(yt_c / y2_c) - 1.0
    elif loss_type == "mse":
        loss1 = (y_true - y_pred1) ** 2
        loss2 = (y_true - y_pred2) ** 2
    else:  # mae
        loss1 = np.abs(y_true - y_pred1)
        loss2 = np.abs(y_true - y_pred2)
        
    # Differential loss series d_t = Loss(Model 1) - Loss(Model 2)
    d = loss1 - loss2
    d_mean = np.mean(d)
    
    # Autocovariance estimation (Newey-West / Bartlett lag window)
    gamma_0 = np.var(d, ddof=0)
    gamma_sum = 0.0
    
    for lag in range(1, h):
        weight = 1.0 - (lag / h)  # Bartlett kernel
        gamma_k = np.cov(d[lag:], d[:-lag])[0, 1] if len(d) > lag else 0.0
        gamma_sum += weight * gamma_k
        
    lr_var = (gamma_0 + 2.0 * gamma_sum) / T
    if lr_var <= 1e-12:
        if abs(d_mean) > 1e-8:
            # Deterministic outperformance
            dm_stat = -10.0 if d_mean < 0 else 10.0
            p_value = 0.0001
        else:
            dm_stat = 0.0
            p_value = 1.0
    else:
        dm_stat = float(d_mean / np.sqrt(lr_var))
        # Two-tailed standard normal test
        p_value = float(2.0 * (1.0 - stats.norm.cdf(np.abs(dm_stat))))
        
    is_significant = p_value < alpha
    if is_significant:
        # If dm_stat < 0, Model 1 has lower loss -> Model 1 is better
        better_model = "model_1" if dm_stat < 0 else "model_2"
    else:
        better_model = "equivalent"
        
    return {
        "dm_stat": round(dm_stat, 4),
        "p_value": round(p_value, 4),
        "is_significant": is_significant,
        "better_model": better_model
    }
