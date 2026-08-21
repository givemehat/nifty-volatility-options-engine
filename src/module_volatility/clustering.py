"""
Correlation Clustering and Sector Grouping for Cluster-HAR and Sector-HAR Volatility Models.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from typing import Dict, List, Tuple
from src.config import SECTOR_MAP

def build_correlation_clusters(
    universe_rv_dict: Dict[str, pd.DataFrame],
    n_clusters: int = 3
) -> Tuple[Dict[str, int], pd.DataFrame]:
    """
    Cluster stocks by their historical daily return / realized volatility correlations.
    Returns:
        cluster_map: Dict mapping symbol -> cluster_id (int)
        corr_matrix: DataFrame of pairwise correlation matrix
    """
    # Build aligned price return or RV pivot table
    aligned_series = {}
    for symbol, df in universe_rv_dict.items():
        if not df.empty and "rv_daily" in df.columns and "date" in df.columns:
            s = df.set_index("date")["rv_daily"]
            aligned_series[symbol] = s

    if not aligned_series:
        return {}, pd.DataFrame()

    df_pivot = pd.DataFrame(aligned_series).dropna(how="all").ffill().bfill()
    symbols = list(df_pivot.columns)

    if len(symbols) < n_clusters:
        # Fallback if fewer symbols than clusters
        cluster_map = {sym: idx for idx, sym in enumerate(symbols)}
        return cluster_map, df_pivot.corr()

    # Compute correlation matrix
    corr_matrix = df_pivot.corr().fillna(0.0)

    # Convert correlation to distance metric: d = sqrt(2 * (1 - r))
    dist_matrix = np.sqrt(np.maximum(0.0, 2.0 * (1.0 - corr_matrix.values)))

    # Agglomerative clustering with precomputed distance matrix
    clustering = AgglomerativeClustering(
        n_clusters=min(n_clusters, len(symbols)),
        metric="precomputed",
        linkage="average"
    )
    cluster_labels = clustering.fit_predict(dist_matrix)

    cluster_map = {symbols[i]: int(cluster_labels[i]) for i in range(len(symbols))}
    return cluster_map, corr_matrix

def compute_cluster_rv_series(
    universe_rv_dict: Dict[str, pd.DataFrame],
    cluster_map: Dict[str, int]
) -> Dict[int, pd.DataFrame]:
    """
    Compute daily average Realized Variance for each cluster.
    """
    cluster_dfs: Dict[int, List[pd.DataFrame]] = {}
    for sym, cluster_id in cluster_map.items():
        if sym in universe_rv_dict and not universe_rv_dict[sym].empty:
            cluster_dfs.setdefault(cluster_id, []).append(universe_rv_dict[sym])

    cluster_rv_series = {}
    for cluster_id, dfs in cluster_dfs.items():
        concat_df = pd.concat(dfs, ignore_index=True)
        avg_df = concat_df.groupby("date")["rv_daily"].mean().reset_index()
        avg_df.rename(columns={"rv_daily": "cluster_rv"}, inplace=True)
        cluster_rv_series[cluster_id] = avg_df

    return cluster_rv_series

def compute_sector_rv_series(
    universe_rv_dict: Dict[str, pd.DataFrame],
    sector_map: Dict[str, str] = SECTOR_MAP
) -> Dict[str, pd.DataFrame]:
    """
    Compute daily average Realized Variance for each industrial sector.
    """
    sector_dfs: Dict[str, List[pd.DataFrame]] = {}
    for sym, sector in sector_map.items():
        if sym in universe_rv_dict and not universe_rv_dict[sym].empty:
            sector_dfs.setdefault(sector, []).append(universe_rv_dict[sym])

    sector_rv_series = {}
    for sector, dfs in sector_dfs.items():
        concat_df = pd.concat(dfs, ignore_index=True)
        avg_df = concat_df.groupby("date")["rv_daily"].mean().reset_index()
        avg_df.rename(columns={"rv_daily": "sector_rv"}, inplace=True)
        sector_rv_series[sector] = avg_df

    return sector_rv_series
