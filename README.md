# NIFTY Volatility & Options Liquidity Engine

A quantitative research and options liquidity platform engineered for Indian index and equity markets (NIFTY 50, BANK NIFTY, and liquid NSE equities). Built with **embedded DuckDB / Parquet**, a decoupled **FastAPI** backend with **SlowAPI rate limiting**, and an interactive **Streamlit** dashboard.

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
git clone https://github.com/givemehat/nifty-volatility-options-engine.git
cd nifty-volatility-options-engine

# Create virtual environment & install requirements
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Batch Ingestion & Model Pipeline
```bash
# Ingests intraday data, fits HAR & ML models, scores options, and populates DuckDB
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

## 🧪 Mathematical Formulations & Modules

### Module 1: Realized Volatility Forecasting

#### 1. High-Frequency Log Returns & Realized Variance ($RV_t$)
Given intraday price observations $P_{t,i}$ sampled at 5-minute intervals ($i = 1, \dots, M$):

$$r_{t,i} = \ln\left(\frac{P_{t,i}}{P_{t,i-1}}\right)$$

The daily Realized Variance is computed as:

$$RV_t = \sum_{i=1}^{M} r_{t,i}^2$$

Annualized Realized Volatility:

$$\sigma_{\text{ann}, t} = \sqrt{252 \times RV_t}$$

#### 2. Jump Robust Variation & Jump Decomposition
Using the Barndorff-Nielsen and Shephard (2004) Bipower Variation ($BV_t$) estimator with $\mu_1 = \sqrt{\frac{2}{\pi}}$:

$$BV_t = \mu_1^{-2} \sum_{i=2}^{M} |r_{t,i}| \cdot |r_{t,i-1}| = \frac{\pi}{2} \sum_{i=2}^{M} |r_{t,i}| \cdot |r_{t,i-1}|$$

The continuous jump variation component ($J_t$) is isolated as:

$$J_t = \max(0, RV_t - BV_t)$$

#### 3. Heterogeneous Autoregressive (HAR-RV) Models
The multi-scale HAR-RV model (Corsi, 2009) decomposes volatility memory into daily, weekly, and monthly cascade components:

$$RV_{t}^{(w)} = \frac{1}{5} \sum_{k=0}^{4} RV_{t-k}, \quad RV_{t}^{(m)} = \frac{1}{22} \sum_{k=0}^{21} RV_{t-k}$$

- **Standard HAR**:
  $$RV_{t+1} = \beta_0 + \beta_d RV_t + \beta_w RV_t^{(w)} + \beta_m RV_t^{(m)} + \varepsilon_{t+1}$$

- **Cluster-HAR (Correlation Spillover)**:
  $$RV_{t+1, i} = \beta_0 + \beta_d RV_{t, i} + \beta_w RV_{t, i}^{(w)} + \beta_m RV_{t, i}^{(m)} + \gamma_c \overline{RV}_{t, \text{cluster}(i)} + \varepsilon_{t+1, i}$$

- **Sector-HAR (Sector Contagion)**:
  $$RV_{t+1, i} = \beta_0 + \beta_d RV_{t, i} + \beta_w RV_{t, i}^{(w)} + \beta_m RV_{t, i}^{(m)} + \gamma_s \overline{RV}_{t, \text{sector}(i)} + \varepsilon_{t+1, i}$$

- **PCA-HAR-Backfill**:
  Decomposes standardized feature matrix $X \in \mathbb{R}^{T \times K}$ into principal components $Z = X V_k$ ($k \le 3$), fits regression on orthogonal factors, and backfills missing/noisy historical series via inverse reconstruction $\hat{X} = Z V_k^T$.

#### 4. Asymmetric Loss & Diebold-Mariano Hypothesis Testing
Models are evaluated on out-of-sample data using the Patton (2011) robust Quasi-Likelihood ($QLIKE$) loss:

$$\mathcal{L}_{QLIKE}(y_t, \hat{y}_t) = \frac{y_t}{\hat{y}_t} - \ln\left(\frac{y_t}{\hat{y}_t}\right) - 1$$

To test statistical significance between Model 1 and Model 2, we evaluate the loss differential series $d_t = \mathcal{L}(y_t, \hat{y}_{1,t}) - \mathcal{L}(y_t, \hat{y}_{2,t})$ under the null hypothesis $H_0: \mathbb{E}[d_t] = 0$:

$$DM = \frac{\bar{d}}{\sqrt{\hat{V}(\bar{d})}} \xrightarrow{d} \mathcal{N}(0, 1)$$

Where $\hat{V}(\bar{d}) = \frac{1}{T}\left(\hat{\gamma}_0 + 2 \sum_{k=1}^{h-1} \left(1 - \frac{k}{h}\right) \hat{\gamma}_k\right)$ with Bartlett kernel spectral density weighting.

---

### Module 2: Options Liquidity & Short-Strangle Screener

#### 1. Black-Scholes Greeks & Exact IV Solver
For underlying spot $S$, strike $K$, time-to-expiry $T$, risk-free rate $r$, and volatility $\sigma$:

$$d_1 = \frac{\ln(S / K) + \left(r + \frac{1}{2}\sigma^2\right)T}{\sigma \sqrt{T}}, \quad d_2 = d_1 - \sigma \sqrt{T}$$

$$\Delta_{\text{Call}} = \mathcal{N}(d_1), \quad \Delta_{\text{Put}} = \mathcal{N}(d_1) - 1$$

$$\Gamma = \frac{\phi(d_1)}{S \sigma \sqrt{T}}, \quad \mathcal{V} = \frac{S \phi(d_1) \sqrt{T}}{100}$$

#### 2. Short-Strangle Multi-Factor Ranking Function
Candidates are evaluated using a balanced multi-factor objective:

$$\text{Rank Score} = 0.40 \times \mathcal{S}_{\text{Liquidity}} + 0.35 \times \mathcal{S}_{\text{Risk Safety}} + 0.25 \times \mathcal{S}_{\text{Yield}}$$

Where:
- $\mathcal{S}_{\text{Liquidity}}$ is derived from bid-ask spread efficiency, open interest depth, and traded volume.
- $\mathcal{S}_{\text{Risk Safety}}$ penalizes net delta drift $|\Delta_{\text{Call}} + \Delta_{\text{Put}}|$ and rewards wider wing cushions $\frac{K_{\text{Call}} - K_{\text{Put}}}{S}$.
- $\mathcal{S}_{\text{Yield}}$ normalizes collected premium relative to spot price.

#### 3. Intraday Open Interest Divergence Metric
Detects asymmetric institutional writing and support/resistance zones:

$$\text{Divergence} = \left(\frac{\Delta OI_t}{OI_{t-1}}\right) - \text{sign}(\text{type}) \times 3 \cdot \left(\frac{\Delta S_t}{S_{t-1}}\right)$$

Strikes with $|\text{Divergence}| \ge 20\%$ and significant volume buildup are flagged as institutional accumulation anomalies.
