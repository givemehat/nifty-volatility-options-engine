# AlphaGrey — NIFTY Volatility & Options Liquidity Platform

A quantitative research and options liquidity web application engineered for Indian index and equity markets (NIFTY, BANK NIFTY, top NSE liquid names). Built with **embedded DuckDB / Parquet**, a decoupled **FastAPI** backend with **SlowAPI rate limiting**, and an interactive **Streamlit** dashboard.

---

## 🏛️ System Architecture

```
                               ┌─────────────────────────────┐
                               │  yfinance / NSE Public API  │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        BATCH INGESTION & QUANTITATIVE ENGINE                           │
│                                                                                        │
│   ┌──────────────────────────────────────────┐  ┌──────────────────────────────────┐   │
│   │ Module 1: Realized Volatility            │  │ Module 2: Options Liquidity      │   │
│   │ - 5-min log return RV & BV Jump decomp   │  │ - NSE Option Chain & Greeks      │   │
│   │ - HAR, Cluster-HAR, Sector-HAR           │  │ - Short Strangle Candidate Gen   │   │
│   │ - PCA-HAR-Backfill, LightGBM, XGBoost    │  │ - Liquidity & Risk Multi-Factor  │   │
│   │ - QLIKE loss & Diebold-Mariano Tests     │  │ - Intraday OI Divergence Tracker │   │
│   └──────────────────────────────────────────┘  └──────────────────────────────────┘   │
└─────────────────────────────────────────────┬──────────────────────────────────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │     EMBEDDED STORAGE        │
                               │   DuckDB + Parquet Files    │
                               │  (Zero Managed DB Server)   │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │      FASTAPI BACKEND        │
                               │   - Precomputed Read API    │
                               │   - In-memory TTL Cache     │
                               │   - SlowAPI Rate Limiter    │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │     STREAMLIT FRONTEND      │
                               │  - Forecast vs Realized UI  │
                               │  - DM Test Heatmap          │
                               │  - Short-Strangle Screener  │
                               │  - Interactive Payoffs      │
                               └─────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone repository
cd Alphagrey

# Create virtual environment & install requirements
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Batch Ingestion & Model Pipeline
```bash
# Ingests data, fits HAR & ML models, scores options, and populates DuckDB
python -m src.jobs.run_batch --module all
```

### 3. Launch Services
You can run the backend and frontend separately or simultaneously:

```bash
# Terminal 1: Run FastAPI Backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Run Streamlit Frontend
streamlit run app/main.py --server.port 8501
```

Access the web interfaces:
- **Streamlit Web App**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 🐳 Docker Deployment

Run the complete 3-tier stack (API, UI, and APScheduler background worker) using `docker-compose`:

```bash
docker-compose up --build -d
```

---

## 🧪 Modules Breakdown

### Module 1: Realized Volatility Forecasting
1. **Intraday Log Returns & Jump Decomposition**:
   - Computes daily Realized Variance $RV_t = \sum r_{t,i}^2$ from 5-min intervals.
   - Bipower Variation (BV) by Barndorff-Nielsen & Shephard: $BV_t = \frac{\pi}{2}\sum |r_{t,i}||r_{t,i-1}|$.
   - Continuous Jump Component $J_t = \max(0, RV_t - BV_t)$.
2. **Forecasting Models**:
   - `HAR`: Standard Heterogeneous Autoregressive model with daily, weekly (5d), and monthly (22d) lags.
   - `Cluster-HAR`: Groups stocks by return-correlation clusters and adds cluster-level volatility spillover.
   - `Sector-HAR`: Adds sector-average volatility contagion.
   - `PCA-HAR-Backfill`: Applies Principal Component Analysis across multi-lag feature space to extract latent market factors and backfills missing history.
   - `LightGBM` & `XGBoost`: Gradient boosted trees capturing non-linear volatility dynamics.
3. **Statistical Evaluation**:
   - $R^2$, RMSE, MAE, and **QLIKE loss** ($QLIKE(y, \hat{y}) = \frac{y}{\hat{y}} - \ln(\frac{y}{\hat{y}}) - 1$).
   - Pairwise **Diebold-Mariano Tests** with Newey-West/Bartlett kernel adjustments for statistical significance.

### Module 2: Options Liquidity & Short-Strangle Screener
1. **Analytical Greeks**: Exact Black-Scholes Delta ($\Delta$), Gamma ($\Gamma$), Vega ($\mathcal{V}$), Theta ($\Theta$), and Brent's root-finding IV solver.
2. **Strangle Candidate Generator**: Filters delta-cushioned OTM strikes ($\Delta \approx 0.10 - 0.25$) and pairs delta-neutral strangles.
3. **Multi-Factor Rank Score**:
   $$\text{Rank Score} = 0.40 \times \text{Liquidity Score} + 0.35 \times \text{Risk Safety Score} + 0.25 \times \text{Premium Yield Score}$$
4. **Intraday OI Divergence Tracker**: Measures rate of change of Open Interest relative to underlying spot trajectory to flag anomalous institutional writing zones.
