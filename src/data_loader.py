"""
data_loader.py
Descarrega e faz cache local dos dados abertos do StatsBomb.

Uso:
    python src/data_loader.py --competition_id 2 --season_id 27 --out data/raw_events_pl1516.parquet

Podes correr isto para qualquer competição/época disponível em statsbombpy.competitions().
Os eventos são cacheados em disco (parquet) para não teres de repetir downloads.
"""
import argparse
import time
import warnings
from pathlib import Path

import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore")  # silencia o aviso de "open data access only"


def fetch_league_events(competition_id: int, season_id: int, out_path: str, sleep: float = 0.05) -> pd.DataFrame:
    """
    Descarrega os eventos de todos os jogos de uma competição/época e guarda em parquet.
    Se o ficheiro já existir, retoma a partir dos jogos que faltam (por match_id).
    """
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    match_ids = matches["match_id"].tolist()
    print(f"[data_loader] {len(match_ids)} jogos encontrados para competition_id={competition_id}, season_id={season_id}")

    # retoma se já houver cache parcial
    if out_file.exists():
        existing = pd.read_parquet(out_file)
        done_ids = set(existing["match_id"].unique())
        print(f"[data_loader] cache existente encontrado com {len(done_ids)} jogos já processados")
    else:
        existing = pd.DataFrame()
        done_ids = set()

    frames = [existing] if not existing.empty else []
    remaining = [m for m in match_ids if m not in done_ids]
    print(f"[data_loader] a processar {len(remaining)} jogos em falta...")

    for i, mid in enumerate(remaining, 1):
        try:
            ev = sb.events(match_id=mid)
            ev["match_id"] = mid
            frames.append(ev)
        except Exception as e:
            print(f"[data_loader] falhou match_id={mid}: {e}")
            continue

        # guarda incrementalmente a cada 20 jogos, para não perderes tudo se algo falhar
        if i % 20 == 0 or i == len(remaining):
            combined = pd.concat(frames, ignore_index=True, sort=False)
            combined.to_parquet(out_file, index=False)
            print(f"[data_loader] progresso: {i}/{len(remaining)} jogos processados, guardado em {out_file}")

        time.sleep(sleep)

    combined = pd.concat(frames, ignore_index=True, sort=False) if frames else existing
    combined.to_parquet(out_file, index=False)
    print(f"[data_loader] concluído. {combined['match_id'].nunique()} jogos, {len(combined)} eventos totais.")
    return combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--competition_id", type=int, required=True)
    parser.add_argument("--season_id", type=int, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    fetch_league_events(args.competition_id, args.season_id, args.out)
