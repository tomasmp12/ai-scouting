"""
config.py
Define os grupos posicionais e as métricas (features) usadas para calcular
similaridade dentro de cada grupo. As posições do StatsBomb são mapeadas
para grupos mais amplos, porque comparar "Right Back" com "Left Back" ainda
faz sentido, mas comparar um lateral com um médio centro não.
"""

# Mapeia as posições detalhadas do StatsBomb para grupos posicionais amplos
POSITION_GROUP_MAP = {
    "Goalkeeper": "GR",
    "Right Back": "LAT",
    "Left Back": "LAT",
    "Right Wing Back": "LAT",
    "Left Wing Back": "LAT",
    "Center Back": "CB",
    "Right Center Back": "CB",
    "Left Center Back": "CB",
    "Defensive Midfield": "MDC",
    "Left Defensive Midfield": "MDC",
    "Right Defensive Midfield": "MDC",
    "Center Defensive Midfield": "MDC",
    "Center Midfield": "MC",
    "Left Center Midfield": "MC",
    "Right Center Midfield": "MC",
    "Attacking Midfield": "MCO",
    "Left Attacking Midfield": "MCO",
    "Right Attacking Midfield": "MCO",
    "Center Attacking Midfield": "MCO",
    "Right Wing": "EXT",
    "Left Wing": "EXT",
    "Right Midfield": "EXT",
    "Left Midfield": "EXT",
    "Center Forward": "AV",
    "Left Center Forward": "AV",
    "Right Center Forward": "AV",
    "Secondary Striker": "AV",
}

# Métricas (calculadas per 90 minutos) relevantes para cada grupo posicional.
# Todas devem existir como colunas depois do feature_engineering.py
POSITION_METRICS = {
    "GR": [
        "saves_p90",
        "goals_conceded_p90",
        "pass_completion_pct",
        "long_balls_p90",
        "def_actions_outside_box_p90",
    ],
    "CB": [
        "tackles_p90",
        "interceptions_p90",
        "aerials_won_p90",
        "aerial_win_pct",
        "clearances_p90",
        "pass_completion_pct",
        "progressive_passes_p90",
        "fouls_committed_p90",
    ],
    "LAT": [
        "tackles_p90",
        "interceptions_p90",
        "crosses_p90",
        "cross_completion_pct",
        "progressive_passes_p90",
        "progressive_carries_p90",
        "dribbles_completed_p90",
        "pass_completion_pct",
    ],
    "MDC": [
        "tackles_p90",
        "interceptions_p90",
        "pass_completion_pct",
        "progressive_passes_p90",
        "passes_into_final_third_p90",
        "ball_recoveries_p90",
        "fouls_committed_p90",
    ],
    "MC": [
        "progressive_passes_p90",
        "progressive_carries_p90",
        "key_passes_p90",
        "pass_completion_pct",
        "tackles_p90",
        "interceptions_p90",
        "dribbles_completed_p90",
    ],
    "MCO": [
        "key_passes_p90",
        "xa_p90",
        "xg_p90",
        "shots_p90",
        "dribbles_completed_p90",
        "progressive_carries_p90",
        "passes_into_box_p90",
    ],
    "EXT": [
        "dribbles_completed_p90",
        "dribble_success_pct",
        "crosses_p90",
        "cross_completion_pct",
        "key_passes_p90",
        "xa_p90",
        "xg_p90",
        "shots_p90",
        "progressive_carries_p90",
    ],
    "AV": [
        "xg_p90",
        "shots_p90",
        "shot_on_target_pct",
        "goals_p90",
        "aerials_won_p90",
        "dribbles_completed_p90",
        "touches_in_box_p90",
    ],
}

MIN_MINUTES_THRESHOLD = 450  # ~5 jogos completos, para filtrar amostras demasiado pequenas
