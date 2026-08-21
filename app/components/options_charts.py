"""
Interactive Plotly visual components for Options Liquidity, Strangle Payoffs, and OI Divergence.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

def plot_strangle_payoff(profile: Dict[str, Any]) -> go.Figure:
    """
    Interactive P&L payoff diagram for a short strangle setup at expiration.
    """
    fig = go.Figure()

    if not profile or "spot_range" not in profile:
        fig.update_layout(title="No payoff data available")
        return fig

    spots = profile["spot_range"]
    pnls = profile["pnl_profile"]
    spot_val = profile["spot"]
    call_k = profile["call_strike"]
    put_k = profile["put_strike"]
    lower_be = profile["lower_breakeven"]
    upper_be = profile["upper_breakeven"]
    max_prof = profile["max_profit"]

    # Main PnL Line
    fig.add_trace(go.Scatter(
        x=spots,
        y=pnls,
        mode="lines",
        name="Strangle P&L",
        line=dict(color="#00E5FF", width=3.5)
    ))

    # Zero Line
    fig.add_hline(y=0, line_dash="dash", line_color="#757575", annotation_text="Breakeven (0)")

    # Spot Price vertical line
    fig.add_vline(x=spot_val, line_dash="dash", line_color="#FFD700", annotation_text=f"Spot: {spot_val:,.1f}")

    # Breakeven vertical markers
    fig.add_vline(x=lower_be, line_dash="dot", line_color="#FF5252", annotation_text=f"Lower BE: {lower_be:,.1f}")
    fig.add_vline(x=upper_be, line_dash="dot", line_color="#FF5252", annotation_text=f"Upper BE: {upper_be:,.1f}")

    # Strikes vertical markers
    fig.add_vline(x=put_k, line_dash="solid", line_color="rgba(105, 240, 174, 0.4)", annotation_text=f"Put K: {put_k:,.0f}")
    fig.add_vline(x=call_k, line_dash="solid", line_color="rgba(105, 240, 174, 0.4)", annotation_text=f"Call K: {call_k:,.0f}")

    fig.update_layout(
        title=f"Short Strangle Expiration Payoff | Max Credit: ₹{max_prof:,.2f} | Put {int(put_k)} / Call {int(call_k)}",
        xaxis_title="Underlying Spot Price at Expiry (₹)",
        yaxis_title="P&L per Unit (₹)",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=60, b=40),
        height=450,
    )
    return fig

def plot_oi_divergence_chart(df_div: pd.DataFrame) -> go.Figure:
    """
    Bar chart showing intraday OI Divergence metrics across strike ladder.
    """
    fig = go.Figure()
    if df_div.empty:
        fig.update_layout(title="No divergence data available")
        return fig

    df = df_div.sort_values("strike")
    ce_df = df[df["option_type"] == "CE"]
    pe_df = df[df["option_type"] == "PE"]

    # Call Divergence
    if not ce_df.empty:
        fig.add_trace(go.Bar(
            x=ce_df["strike"],
            y=ce_df["divergence_metric"],
            name="Call (CE) Divergence",
            marker_color="#FF5252"
        ))

    # Put Divergence
    if not pe_df.empty:
        fig.add_trace(go.Bar(
            x=pe_df["strike"],
            y=pe_df["divergence_metric"],
            name="Put (PE) Divergence",
            marker_color="#69F0AE"
        ))

    # Highlight Anomalies
    anomalies = df[df["flag_anomaly"] == True]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["strike"],
            y=anomalies["divergence_metric"],
            mode="markers",
            name="⚠️ Unusual Buildup Anomaly",
            marker=dict(symbol="star", size=14, color="#FFD700", line=dict(width=1, color="#FFFFFF"))
        ))

    fig.update_layout(
        title="Intraday OI Divergence vs Price Trajectory (Resistance / Support Buildup)",
        xaxis_title="Strike Price",
        yaxis_title="OI Divergence Metric (%)",
        template="plotly_dark",
        barmode="group",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        height=420,
    )
    return fig

def plot_oi_distribution(df_chain: pd.DataFrame) -> go.Figure:
    """
    Open Interest distribution across strikes for Calls and Puts.
    """
    fig = go.Figure()
    if df_chain.empty:
        return fig

    df = df_chain.sort_values("strike")
    ce_df = df[df["option_type"] == "CE"]
    pe_df = df[df["option_type"] == "PE"]

    if not ce_df.empty:
        fig.add_trace(go.Bar(
            x=ce_df["strike"],
            y=ce_df["open_interest"],
            name="Call Open Interest",
            marker_color="rgba(255, 82, 82, 0.7)"
        ))

    if not pe_df.empty:
        fig.add_trace(go.Bar(
            x=pe_df["strike"],
            y=pe_df["open_interest"],
            name="Put Open Interest",
            marker_color="rgba(105, 240, 174, 0.7)"
        ))

    fig.update_layout(
        title="Open Interest Depth Ladder (Calls vs Puts)",
        xaxis_title="Strike Price",
        yaxis_title="Open Interest (Contracts)",
        template="plotly_dark",
        barmode="group",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        height=380,
    )
    return fig
