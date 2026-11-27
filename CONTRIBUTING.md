# ❄️ Contributing to VolVantage (NIFTY Volatility & Options Engine)

Welcome to **VolVantage**! We are thrilled to participate in **Winter of Code Social (WOCS) 2026** as an accepted open-source project. 

Whether you are making your first open-source pull request or you are an experienced quant developer, we welcome your contributions!

---

## 📋 Table of Contents
1. [Code of Conduct](#-code-of-conduct)
2. [Winter of Code Social (WOCS) 2026 Guidelines](#-winter-of-code-social-wocs-2026-guidelines)
3. [Points & Difficulty Levels](#-points--difficulty-levels)
4. [AI Policy](#-ai-policy)
5. [How to Contribute Step-by-Step](#-how-to-contribute-step-by-step)
6. [Local Environment Setup](#-local-environment-setup)
7. [Coding Standards & Commit Conventions](#-coding-standards--commit-conventions)
8. [Getting Help & Community](#-getting-help--community)

---

## 🤝 Code of Conduct
We are committed to providing a welcoming, inclusive, and harassment-free environment for all contributors. Please be respectful, constructive, and supportive in all discussions and reviews.

---

## ❄️ Winter of Code Social (WOCS) 2026 Guidelines

To ensure your contributions count toward the **[WOCS Leaderboard](https://woc.codesocial.tech/leaderboard)**:

1. **Be Registered:** You must be officially registered on the [WOCS Website](https://woc.codesocial.tech).
2. **Find an Issue:** Browse open issues with the `wocs` label on our [Issue Tracker](https://github.com/givemehat/nifty-volatility-options-engine/issues).
3. **Claiming an Issue:** Comment on the issue expressing your interest (e.g., *"Hi @givemehat, I'd like to work on this issue under WOCS 2026!"*). Wait for assignment before starting work to avoid duplicate efforts.
4. **Required PR Labels:** Every qualifying pull request will be assigned:
   - `wocs`
   - One difficulty level: `level 1`, `level 2`, or `level 3`
   *(Labels will be applied by Project Admins / Mentors before merging. Merged PRs without these labels cannot be tracked by the webhook!)*

---

## 🏆 Points & Difficulty Levels

| Level | Description | WOCS Points |
| :--- | :--- | :---: |
| **`level 1`** | Beginner-friendly tasks: documentation, typo fixes, UI styling, adding sample test cases. | **2 Points** |
| **`level 2`** | Moderate tasks: new dashboard features, options metrics calculation, API endpoint validation, refactoring. | **5 Points** |
| **`level 3`** | Complex / Architectural tasks: new statistical volatility models, DuckDB OLAP optimization, sub-millisecond Greeks solvers, WebSocket feeds. | **11 Points** |

---

## 🤖 AI Policy

We believe in disciplined engineering:
- **Allowed:** You may use AI assistants (ChatGPT, Claude, Copilot, Gemini) for ideation, syntax lookup, debugging, or writing boilerplate.
- **Mandatory:** You must **thoroughly understand every line of code** you submit. Your code must be clean, correctly typed, documented, and covered by passing unit tests.
- **Prohibited:** Blind copy-pasting of hallucinated, broken, or untested code is strictly prohibited. Submissions with unverified AI hallucinations will be rejected.

---

## 🚀 How to Contribute Step-by-Step

### 1. Fork & Clone
```bash
git clone https://github.com/<your-username>/nifty-volatility-options-engine.git
cd nifty-volatility-options-engine
```

### 2. Create a Feature Branch
```bash
git checkout -b feat/your-feature-name
# or for bug fixes:
git checkout -b fix/issue-description
```

### 3. Set Up Local Environment
```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Local Test Suite
```bash
pytest tests/ -v
```

### 5. Commit with Conventional Commits
```bash
git commit -m "feat(options): add put-call ratio divergence indicator (#12)"
```

### 6. Push and Open a Pull Request
- Push to your fork: `git push origin feat/your-feature-name`
- Open a Pull Request against `givemehat/nifty-volatility-options-engine` on branch `main`.
- In the PR description, reference your issue: `Fixes #<issue-number>`.
- Mention that this contribution is part of **WOCS 2026**.

---

## 🛠️ Tech Stack & Directory Structure

- **Python 3.11+**: Core modeling and statistical estimation
- **FastAPI**: Asynchronous high-throughput REST backend
- **DuckDB**: Fast in-process analytical SQL & Parquet engine
- **Plotly.js / Streamlit**: Interactive visualization & UI dashboard
- **pytest**: Automated testing suite

```
nifty-volatility-options-engine/
├── app/               # FastAPI REST application & routers
├── src/               # Econometric models (HAR, LightGBM, Options Screener)
├── tests/             # Unit and integration test suites
├── frontend/          # Web dashboard and UI components
├── index.html         # Live GitHub Pages visualization
├── requirements.txt   # Python dependency specifications
└── CONTRIBUTING.md    # Contribution guidelines
```

---

## 💬 Community & Support

- **Discord:** Join the [Code Social Discord Server](https://discord.gg/MSTNyRSPYW).
- **Project Forum:** Find our project thread under the `#find-a-project` channel.
- **Questions?** Feel free to ask in the issue discussion or reach out to Project Admin **[@givemehat](https://github.com/givemehat)** (`rajnisihsingh@gmail.com`).

Happy Contributing and welcome to Winter of Code Social 2026! ❄️🚀
