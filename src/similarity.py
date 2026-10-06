"""
similarity.py
Motor de similaridade de jogadores: dado um jogador de referência, devolve
os N jogadores mais parecidos dentro do mesmo grupo posicional, usando
z-scores das métricas relevantes e distância de cosseno.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

from config import POSITION_METRICS


def compute_similarity_table(stats: pd.DataFrame, position_group: str):
    """
    Para um dado grupo posicional, normaliza as métricas relevantes (z-score)
    e devolve a submatriz de jogadores + a matriz de similaridade de cosseno.
    """
    metrics = POSITION_METRICS[position_group]
    sub = stats[stats["position_group"] == position_group].copy().reset_index(drop=True)

    if sub.empty:
        return sub, np.array([])

    X = sub[metrics].fillna(0.0).values
    X_scaled = StandardScaler().fit_transform(X)
    sim_matrix = cosine_similarity(X_scaled)
    return sub, sim_matrix


def find_similar_players(
    stats: pd.DataFrame,
    player_name: str,
    top_n: int = 5,
    max_age=None,
    exclude_same_player: bool = True,
) -> pd.DataFrame:
    """
    Encontra os jogadores mais parecidos com `player_name`, dentro do mesmo
    grupo posicional. Devolve um DataFrame com o score de similaridade (0-1).
    """
    row = stats[stats["player"] == player_name]
    if row.empty:
        raise ValueError(f"Jogador '{player_name}' não encontrado na tabela de estatísticas.")

    position_group = row.iloc[0]["position_group"]
    sub, sim_matrix = compute_similarity_table(stats, position_group)

    idx = sub.index[sub["player"] == player_name][0]
    scores = sim_matrix[idx]

    result = sub.copy()
    result["similarity"] = scores

    if exclude_same_player:
        result = result[result["player"] != player_name]

    if max_age is not None and "age" in result.columns:
        result = result[result["age"] <= max_age]

    result = result.sort_values("similarity", ascending=False).head(top_n)
    metrics = POSITION_METRICS[position_group]
    return result[["player", "position", "position_group", "total_minutes", "similarity"] + metrics]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", type=str, required=True)
    parser.add_argument("--player", type=str, required=True)
    parser.add_argument("--top_n", type=int, default=5)
    args = parser.parse_args()

    stats = pd.read_parquet(args.stats)
    res = find_similar_players(stats, args.player, top_n=args.top_n)
    print(res.to_string(index=False))
