"""
Interactive Plotly visual components for Realized Volatility and Diebold-Mariano tests.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Optional

def plot_forecast_vs_realized(df_forecasts: pd.DataFrame, selected_models: Optional[List[str]] = None) -> go.Figure:
    """
    Line chart comparing out-of-sample volatility forecasts against actual realized volatility.
    """
    fig = go.Figure()

    if df_forecasts.empty:
        fig.update_layout(title="No forecast data available")
        return fig

    # Get distinct actual RV/vol
    first_model = df_forecasts["model_name"].iloc[0]
    actual_data = df_forecasts[df_forecasts["model_name"] == first_model].sort_values("date")

    # Add Actual Realized Volatility line
    fig.add_trace(go.Scatter(
        x=actual_data["date"],
        y=actual_data["actual_vol"] * 100.0,
        mode="lines+markers",
        name="Actual Realized Vol (%)",
        line=dict(color="#00E5FF", width=3.5),
        marker=dict(size=6, symbol="circle")
    ))

    # Add each selected model's forecast
    available_models = df_forecasts["model_name"].unique()
    models_to_plot = selected_models if selected_models else available_models

    colors = ["#FF5252", "#FFD700", "#69F0AE", "#E040FB", "#40C4FF", "#FFAB40"]
    for i, model in enumerate(models_to_plot):
        m_df = df_forecasts[df_forecasts["model_name"] == model].sort_values("date")
        if not m_df.empty:
            fig.add_trace(go.Scatter(
                x=m_df["date"],
                y=m_df["forecast_vol"] * 100.0,
                mode="lines",
                name=f"{model} Forecast (%)",
                line=dict(dash="dot" if "HAR" in model else "dash", width=2.0, color=colors[i % len(colors)])
            ))

    fig.update_layout(
        title="Out-of-Sample Realized Volatility: Model Forecasts vs Ground Truth",
        xaxis_title="Date",
        yaxis_title="Annualized Volatility (%)",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=480,
    )
    return fig

def plot_rv_decomposition(df_rv: pd.DataFrame) -> go.Figure:
    """
    Time series showing Realized Volatility, Bipower Variation (continuous component), and Jumps.
    """
    fig = go.Figure()
    if df_rv.empty:
        return fig

    df = df_rv.sort_values("date")

    # Realized Volatility Line
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["rv_annualized"] * 100.0,
        name="Total Realized Vol (%)",
        line=dict(color="#00E5FF", width=2.5),
        mode="lines"
    ))

    # Jump component bar
    if "jump_component" in df.columns:
        jump_vol = np.sqrt(df["jump_component"] * 252.0) * 100.0
        fig.add_trace(go.Bar(
            x=df["date"],
            y=jump_vol,
            name="Jump Component (Vol %)",
            marker_color="rgba(255, 82, 82, 0.6)",
        ))

    fig.update_layout(
        title="Realized Volatility & Jump Variation Decomposition",
        xaxis_title="Date",
        yaxis_title="Annualized Volatility (%)",
        template="plotly_dark",
        barmode="overlay",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=380,
    )
    return fig

def plot_dm_heatmap(df_dm: pd.DataFrame) -> go.Figure:
    """
    Pairwise Diebold-Mariano test p-value heatmap.
    Statistically significant differences (p < 0.05) are highlighted.
    """
    if df_dm.empty:
        fig = go.Figure()
        fig.update_layout(title="No DM test data available")
        return fig

    models = sorted(list(set(df_dm["model_1"].unique()).union(set(df_dm["model_2"].unique()))))
    matrix_p = pd.DataFrame(index=models, columns=models, data=1.0)
    matrix_text = pd.DataFrame(index=models, columns=models, data="")

    for _, row in df_dm.iterrows():
        m1 = row["model_1"]
        m2 = row["model_2"]
        p_val = float(row["p_value"])
        stat = float(row["dm_stat"])
        sig = bool(row["is_significant"])
        better = str(row["better_model"])

        if m1 in models and m2 in models:
            matrix_p.loc[m1, m2] = p_val
            if m1 == m2:
                matrix_text.loc[m1, m2] = "-"
            else:
                star = "★ " if sig else ""
                matrix_text.loc[m1, m2] = f"{star}p={p_val:.3f}<br>DM={stat:.2f}"

    fig = go.Figure(data=go.Heatmap(
        z=matrix_p.values,
        x=models,
        y=models,
        text=matrix_text.values,
        texttemplate="%{text}",
        textfont={"size": 11},
        colorscale=[[0, "#00E676"], [0.05, "#FFEB3B"], [0.2, "#FF5722"], [1.0, "#212121"]],
        colorbar=dict(title="p-value (QLIKE)"),
        zmin=0.0,
        zmax=0.5
    ))

    fig.update_layout(
        title="Pairwise Diebold-Mariano Test Matrix (★ indicates p < 0.05 significance)",
        xaxis_title="Model 2 (Benchmark)",
        yaxis_title="Model 1 (Candidate)",
        template="plotly_dark",
        height=450,
        margin=dict(l=60, r=40, t=60, b=40),
    )
    return fig
