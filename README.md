# AI Scouting — Motor de Similaridade de Jogadores

Protótipo de scouting inteligente: dado um jogador de referência, encontra
alternativas estatisticamente parecidas dentro do mesmo grupo posicional —
a base para "encontra o próximo [jogador], mais barato".

## Estrutura do projeto

```
ai-scouting/
├── data/                  # dados brutos e processados (cache local, não vai para git)
├── src/
│   ├── config.py           # grupos posicionais e métricas por grupo
│   ├── data_loader.py       # descarrega e faz cache dos eventos do StatsBomb Open Data
│   ├── feature_engineering.py  # transforma eventos em stats por jogador/90min
│   └── similarity.py        # motor de similaridade (z-score + cosine similarity)
├── app/
│   └── app.py               # app Streamlit interativa
├── requirements.txt
└── README.md
```

## Como correr

```bash
# 1. instalar dependências
pip install -r requirements.txt

# 2. descarregar dados (StatsBomb Open Data — Premier League 2015/16, época completa)
python src/data_loader.py --competition_id 2 --season_id 27 --out data/raw_events_pl1516.parquet

# 3. gerar tabela de estatísticas por jogador
python src/feature_engineering.py --events data/raw_events_pl1516.parquet --out data/player_stats_pl1516.parquet

# 4. correr a app
streamlit run app/app.py
```

Também podes testar o motor de similaridade diretamente na linha de comandos:

```bash
python src/similarity.py --stats data/player_stats_pl1516.parquet --player "Mesut Özil" --top_n 5
```

## Porque Premier League 2015/16?

É a única época no StatsBomb Open Data com **cobertura completa** (380 jogos,
todas as 20 equipas) disponível gratuitamente — a maioria das outras épocas
(La Liga 2020/21, Bundesliga 2023/24, etc.) só inclui os jogos de uma equipa
específica. Isto dá-nos amostras de minutos muito mais fiáveis para todas as
posições.

Para trocar de liga/época, basta mudar `competition_id`/`season_id` — consulta
`statsbombpy.sb.competitions()` para ver as opções disponíveis.

## Limitações atuais (importante para a apresentação ao clube)

- **Dados abertos, não dados de tracking/360.** Métricas como xA real,
  carries progressivos e ações defensivas fora de área estão marcadas como
  placeholder porque exigem dados posicionais (tracking data) que só vêm com
  fontes pagas (Wyscout, Opta, InStat) ou parcerias de dados do próprio clube.
- **Cobertura de ligas.** Não há dados abertos para a Liga Portugal ou ligas
  secundárias — este protótipo demonstra o conceito com uma liga de topo.
  Com acesso à API paga do clube (que muitos já têm), o mesmo pipeline aplica-se
  diretamente às ligas relevantes para eles.
- **Minutos mínimos.** Jogadores com poucos minutos são filtrados
  (`MIN_MINUTES_THRESHOLD` em `config.py`) para evitar comparações com
  amostras estatísticas pequenas.

## Próximos passos possíveis

- Adicionar filtro de idade e valor de mercado estimado (via scraping do
  Transfermarkt, por exemplo).
- Migrar de cosine similarity para um modelo mais sofisticado (ex: PCA +
  clustering, ou embeddings aprendidos).
- Adicionar exportação de relatório em PDF por jogador.
- Ligar a uma fonte de dados paga quando houver orçamento/parceria.
