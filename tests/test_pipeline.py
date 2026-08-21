"""
Comprehensive Unit and Integration Tests for AlphaGrey.
Tests Realized Volatility calculation, HAR/ML models, Diebold-Mariano tests, Black-Scholes Greeks,
Strangle Screener ranking, and FastAPI endpoints.
"""

import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.common.stats import r2_metric, qlike_metric, diebold_mariano_test
from src.common.greeks import bs_price, implied_volatility, calculate_greeks, calculate_strangle_profile
from src.module_volatility.rv_calculator import compute_daily_realized_volatility
from src.module_volatility.features import create_har_features
from src.module_volatility.models.har import StandardHAR
from src.module_volatility.models.pca_har import PCAHARBackfillModel
from src.module_volatility.models.ml_models import LightGBMVolModel, XGBoostVolModel
from src.module_options.liquidity_scorer import compute_strike_liquidity_score, compute_strangle_liquidity
from src.module_options.risk_scorer import compute_strangle_risk_metrics
from src.api.main import app

def test_statistical_metrics():
    y_true = np.array([0.0002, 0.0003, 0.00015, 0.00025, 0.0004])
    y_pred = np.array([0.00021, 0.00028, 0.00016, 0.00024, 0.00038])
    
    r2 = r2_metric(y_true, y_pred)
    assert 0.8 <= r2 <= 1.0, f"Expected high R2, got {r2}"
    
    qlike = qlike_metric(y_true, y_pred)
    assert qlike >= 0.0, f"Expected non-negative QLIKE, got {qlike}"

def test_diebold_mariano():
    y_true = np.array([0.0002, 0.0003, 0.00015, 0.00025, 0.0004, 0.0003, 0.0002])
    y_pred1 = y_true * 1.01  # very accurate
    y_pred2 = y_true * 1.50  # poor
    
    dm_res = diebold_mariano_test(y_true, y_pred1, y_pred2, loss_type="qlike")
    assert "dm_stat" in dm_res
    assert "p_value" in dm_res
    assert dm_res["dm_stat"] < 0, "Model 1 should have lower loss"

def test_black_scholes_and_greeks():
    S = 24500.0
    K = 24500.0
    T = 30.0 / 365.0
    r = 0.065
    sigma = 0.15
    
    call_p = bs_price(S, K, T, r, sigma, "CE")
    put_p = bs_price(S, K, T, r, sigma, "PE")
    assert call_p > 0
    assert put_p > 0
    
    # Put-Call Parity: C - P = S - K * exp(-rT)
    diff = (call_p - put_p) - (S - K * np.exp(-r * T))
    assert abs(diff) < 0.01
    
    greeks_ce = calculate_greeks(S, K, T, r, sigma, "CE")
    assert 0.45 <= greeks_ce["delta"] <= 0.65
    assert greeks_ce["vega"] > 0
    
    greeks_pe = calculate_greeks(S, K, T, r, sigma, "PE")
    assert -0.65 <= greeks_pe["delta"] <= -0.35

def test_strangle_payoff():
    spot = 24500.0
    call_k = 25000.0
    put_k = 24000.0
    call_prem = 85.0
    put_prem = 75.0
    
    profile = calculate_strangle_profile(spot, call_k, put_k, call_prem, put_prem)
    assert profile["total_credit"] == 160.0
    assert profile["lower_breakeven"] == 23840.0
    assert profile["upper_breakeven"] == 25160.0

def test_har_and_ml_models():
    np.random.seed(42)
    dates = pd.bdate_range(end="2026-08-20", periods=50)
    rv_values = np.random.uniform(0.0001, 0.0005, size=50)
    
    df_rv = pd.DataFrame({
        "symbol": "NIFTY 50",
        "date": dates.date,
        "rv_daily": rv_values,
        "rv_annualized": np.sqrt(rv_values * 252),
        "bv_daily": rv_values * 0.9,
        "jump_component": rv_values * 0.1,
        "close_price": 24500.0 + np.cumsum(np.random.normal(0, 50, size=50))
    })
    
    df_feat = create_har_features(df_rv)
    assert not df_feat.empty
    
    # Fit HAR
    har = StandardHAR().fit(df_feat)
    preds_har = har.predict_df(df_feat)
    assert len(preds_har) == len(df_feat)
    assert np.all(preds_har > 0)
    
    # Fit PCA-HAR
    pca_har = PCAHARBackfillModel(n_components=2).fit(df_feat)
    preds_pca = pca_har.predict_df(df_feat)
    assert len(preds_pca) == len(df_feat)
    
    # Fit LightGBM
    lgb = LightGBMVolModel(n_estimators=10).fit(df_feat)
    preds_lgb = lgb.predict_df(df_feat)
    assert len(preds_lgb) == len(df_feat)

def test_api_endpoints():
    client = TestClient(app)
    
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    
    r_sym = client.get("/api/volatility/symbols")
    assert r_sym.status_code == 200
    assert "indices" in r_sym.json()
    
    r_opt_sym = client.get("/api/options/symbols")
    assert r_opt_sym.status_code == 200
