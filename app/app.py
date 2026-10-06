"""
app.py
App Streamlit: "Encontra o próximo [jogador]".
O utilizador escolhe um jogador de referência, define filtros (idade, minutos
mínimos), e a app devolve os jogadores mais parecidos dentro do mesmo grupo
posicional, com um radar chart comparativo.

Corre com:
    streamlit run app/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from mplsoccer import Radar
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import POSITION_METRICS  # noqa: E402
from similarity import find_similar_players  # noqa: E402

st.set_page_config(page_title="Deep XI - Your AI Scouter", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "player_stats_pl1516.parquet"


@st.cache_data
def load_stats():
    return pd.read_parquet(DATA_PATH)


st.title("Deep XI — Beyond the eye test")
st.caption(
    "Smart Scouting: Find statistically similar alternatives to any benchmark player based on their positional profiles. Powered by StatsBomb data (limited to Premier League and 2015/16 season)"
)

if not DATA_PATH.exists():
    st.error(
        f"Não encontrei o ficheiro de estatísticas em {DATA_PATH}. "
        "Corre primeiro src/data_loader.py e src/feature_engineering.py."
    )
    st.stop()

stats = load_stats()

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    player = st.selectbox("Jogador de referência", sorted(stats["player"].unique()))
with col2:
    top_n = st.slider("Nº de jogadores parecidos", min_value=3, max_value=10, value=5)
with col3:
    min_minutes = st.slider("Minutos mínimos jogados", 450, 3000, 900, step=90)

filtered_stats = stats[stats["total_minutes"] >= min_minutes]

if st.button("Procurar jogadores parecidos", type="primary"):
    try:
        results = find_similar_players(filtered_stats, player, top_n=top_n)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    st.subheader(f"Jogadores mais parecidos com {player}")
    display_cols = ["player", "position", "similarity", "total_minutes"]
    pretty = results[display_cols].copy()
    pretty["similarity"] = (pretty["similarity"] * 100).round(1).astype(str) + "%"
    pretty["total_minutes"] = pretty["total_minutes"].round(0).astype(int)
    pretty.columns = ["Jogador", "Posição", "Similaridade", "Minutos jogados"]
    st.dataframe(pretty, use_container_width=True, hide_index=True)

    # Radar chart comparativo: jogador de referência vs. o mais parecido
    position_group = stats[stats["player"] == player].iloc[0]["position_group"]
    metrics = POSITION_METRICS[position_group]

    ref_row = stats[stats["player"] == player].iloc[0]
    top_match = results.iloc[0]

    st.subheader(f"Comparação: {player} vs. {top_match['player']}")

    low = [stats[m].quantile(0.05) for m in metrics]
    high = [stats[m].quantile(0.95) for m in metrics]
    radar = Radar(metrics, low, high, round_int=[False] * len(metrics), num_rings=4)

    fig, ax = radar.setup_axis(figsize=(8, 8))
    radar.draw_circles(ax=ax, facecolor="#e8e8e8")
    radar.draw_radar_compare(
        [ref_row[m] for m in metrics],
        [top_match[m] for m in metrics],
        ax=ax,
        kwargs_radar={"facecolor": "#1a78cf", "alpha": 0.6},
        kwargs_compare={"facecolor": "#d70232", "alpha": 0.6},
    )
    radar.draw_range_labels(ax=ax, fontsize=7)
    radar.draw_param_labels(ax=ax, fontsize=8)

    import matplotlib.patches as mpatches
    blue_patch = mpatches.Patch(color="#1a78cf", alpha=0.6, label=player)
    red_patch = mpatches.Patch(color="#d70232", alpha=0.6, label=top_match["player"])
    fig.legend(
        handles=[blue_patch, red_patch],
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.02),
        frameon=False,
        fontsize=10,
    )
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    st.caption(
        "⚠️ Protótipo com dados abertos (StatsBomb Open Data, Premier League 2015/16). "
        "Algumas métricas (xA, carries progressivos, ações defensivas fora de área) "
        "dependem de dados de tracking/360 e estão marcadas como placeholder — "
        "seriam preenchidas com acesso a uma fonte de dados paga (Wyscout, Opta) ou dados internos do clube."
    )
