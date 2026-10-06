"""
feature_engineering.py
Transforma os eventos brutos do StatsBomb (uma linha por evento) numa tabela
agregada: uma linha por jogador, com estatísticas normalizadas por 90 minutos
e a sua posição principal / grupo posicional.

Uso:
    python src/feature_engineering.py --events data/raw_events_pl1516.parquet --out data/player_stats_pl1516.parquet
"""
import argparse
import warnings

import numpy as np
import pandas as pd

from config import POSITION_GROUP_MAP, MIN_MINUTES_THRESHOLD

warnings.filterwarnings("ignore")


def compute_minutes_played(events: pd.DataFrame) -> pd.DataFrame:
    """
    Estima os minutos jogados por jogador por jogo a partir dos eventos
    'Starting XI', 'Substitution' e do fim do jogo.
    """
    minutes = []
    for match_id, match_ev in events.groupby("match_id"):
        match_end = match_ev["minute"].max() + 1  # aproximação simples

        starters = match_ev[match_ev["type"] == "Starting XI"]
        subs_off = match_ev[match_ev["type"] == "Substitution"]

        lineup_players = set()
        for _, row in starters.iterrows():
            lineup = row.get("tactics", {})
            if isinstance(lineup, dict):
                for p in lineup.get("lineup", []):
                    lineup_players.add(p["player"]["name"])

        player_minutes = {p: match_end for p in lineup_players}

        for _, row in subs_off.iterrows():
            player_out = row.get("player")
            player_in = row.get("substitution_replacement")
            minute = row.get("minute", match_end)
            if player_out in player_minutes:
                player_minutes[player_out] = minute
            if isinstance(player_in, str):
                player_minutes[player_in] = match_end - minute

        for player, mins in player_minutes.items():
            minutes.append({"match_id": match_id, "player": player, "minutes": max(mins, 0)})

    return pd.DataFrame(minutes)


def safe_ratio(num, den):
    return np.where(den > 0, num / den, 0.0)


def build_player_stats(events: pd.DataFrame) -> pd.DataFrame:
    minutes_df = compute_minutes_played(events)
    total_minutes = minutes_df.groupby("player")["minutes"].sum().rename("total_minutes")

    pos = (
        events.dropna(subset=["position"])
        .groupby(["player", "position"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .drop_duplicates("player")
        .set_index("player")["position"]
    )

    df = events.copy()
    df["is_pass"] = df["type"] == "Pass"
    df["pass_complete"] = df["is_pass"] & df["pass_outcome"].isna()
    df["is_progressive_pass"] = df["is_pass"] & (df.get("pass_length", 0).fillna(0) >= 9.11)
    df["is_shot"] = df["type"] == "Shot"
    df["is_goal"] = df["is_shot"] & (df["shot_outcome"] == "Goal")
    df["is_shot_on_target"] = df["is_shot"] & df["shot_outcome"].isin(["Goal", "Saved"])
    df["is_dribble"] = df["type"] == "Dribble"
    df["is_dribble_complete"] = df["is_dribble"] & (df["dribble_outcome"] == "Complete")
    df["is_tackle"] = (df["type"] == "Duel") & (df.get("duel_type", "") == "Tackle")
    df["is_interception"] = df["type"] == "Interception"
    df["is_clearance"] = df["type"] == "Clearance"
    df["is_cross"] = df["is_pass"] & (df.get("pass_cross", False) == True)  # noqa: E712
    df["is_cross_complete"] = df["is_cross"] & df["pass_outcome"].isna()
    df["is_key_pass"] = df.get("pass_shot_assist", False) == True  # noqa: E712
    df["xg"] = df.get("shot_statsbomb_xg", 0.0)
    df["xg"] = df["xg"].fillna(0.0) if "xg" in df else 0.0
    df["is_aerial_won"] = df.get("duel_outcome", "").isin(["Won", "Success In Play", "Success Out"])
    df["is_foul_committed"] = df["type"] == "Foul Committed"
    df["is_recovery"] = df["type"] == "Ball Recovery"

    agg = df.groupby("player").agg(
        passes=("is_pass", "sum"),
        passes_completed=("pass_complete", "sum"),
        progressive_passes=("is_progressive_pass", "sum"),
        shots=("is_shot", "sum"),
        goals=("is_goal", "sum"),
        shots_on_target=("is_shot_on_target", "sum"),
        xg_total=("xg", "sum"),
        dribbles=("is_dribble", "sum"),
        dribbles_completed=("is_dribble_complete", "sum"),
        tackles=("is_tackle", "sum"),
        interceptions=("is_interception", "sum"),
        clearances=("is_clearance", "sum"),
        crosses=("is_cross", "sum"),
        crosses_completed=("is_cross_complete", "sum"),
        key_passes=("is_key_pass", "sum"),
        aerials_won=("is_aerial_won", "sum"),
        fouls_committed=("is_foul_committed", "sum"),
        ball_recoveries=("is_recovery", "sum"),
    )

    agg = agg.join(total_minutes).join(pos.rename("position")).dropna(subset=["total_minutes"])
    agg = agg[agg["total_minutes"] >= MIN_MINUTES_THRESHOLD].copy()

    p90 = agg["total_minutes"] / 90.0
    agg["pass_completion_pct"] = safe_ratio(agg["passes_completed"], agg["passes"]) * 100
    agg["progressive_passes_p90"] = agg["progressive_passes"] / p90
    agg["shots_p90"] = agg["shots"] / p90
    agg["goals_p90"] = agg["goals"] / p90
    agg["xg_p90"] = agg["xg_total"] / p90
    agg["shot_on_target_pct"] = safe_ratio(agg["shots_on_target"], agg["shots"]) * 100
    agg["dribbles_completed_p90"] = agg["dribbles_completed"] / p90
    agg["dribble_success_pct"] = safe_ratio(agg["dribbles_completed"], agg["dribbles"]) * 100
    agg["tackles_p90"] = agg["tackles"] / p90
    agg["interceptions_p90"] = agg["interceptions"] / p90
    agg["clearances_p90"] = agg["clearances"] / p90
    agg["crosses_p90"] = agg["crosses"] / p90
    agg["cross_completion_pct"] = safe_ratio(agg["crosses_completed"], agg["crosses"]) * 100
    agg["key_passes_p90"] = agg["key_passes"] / p90
    agg["aerials_won_p90"] = agg["aerials_won"] / p90
    agg["aerial_win_pct"] = 50.0  # placeholder: precisa de duel_outcome mais detalhado
    agg["fouls_committed_p90"] = agg["fouls_committed"] / p90
    agg["ball_recoveries_p90"] = agg["ball_recoveries"] / p90

    # placeholders para métricas que exigem 360 data / tracking (nem todos os jogos têm)
    for col in ["xa_p90", "progressive_carries_p90", "passes_into_final_third_p90",
                "passes_into_box_p90", "touches_in_box_p90", "saves_p90",
                "goals_conceded_p90", "long_balls_p90", "def_actions_outside_box_p90"]:
        if col not in agg.columns:
            agg[col] = 0.0

    agg["position_group"] = agg["position"].map(POSITION_GROUP_MAP).fillna("OUTRO")
    agg = agg.reset_index()
    return agg


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    events = pd.read_parquet(args.events)
    stats = build_player_stats(events)
    stats.to_parquet(args.out, index=False)
    print(f"[feature_engineering] {len(stats)} jogadores processados -> {args.out}")
    print(stats["position_group"].value_counts())
