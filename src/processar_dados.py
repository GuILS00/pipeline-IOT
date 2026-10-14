
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# Caminho do arquivo CSV.
# Troque NOME_DO_ARQUIVO.csv pelo nome real do arquivo em data.
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "IOT-temp.csv"

# Conexão com o PostgreSQL no Docker.
DATABASE_URL = (
    "postgresql+psycopg2://iot_user:iot_senha_123"
    "@localhost:5433/iot_database"
)

# Verifica se o arquivo existe.
if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"CSV não encontrado: {CSV_PATH}"
    )

# Lê o CSV.
df = pd.read_csv(CSV_PATH)

# Remove espaços extras dos nomes das colunas.
df.columns = df.columns.str.strip()

# Confere se todas as colunas esperadas existem.
colunas_esperadas = [
    "id",
    "room_id/id",
    "noted_date",
    "temp",
    "out/in",
]

colunas_ausentes = [
    coluna
    for coluna in colunas_esperadas
    if coluna not in df.columns
]

if colunas_ausentes:
    raise ValueError(
        f"Colunas ausentes no CSV: {colunas_ausentes}"
    )

# Seleciona e padroniza os nomes das colunas.
df = df[colunas_esperadas].rename(
    columns={
        "id": "reading_id",
        "room_id/id": "device_id",
        "temp": "temperature",
        "out/in": "direction",
    }
)

# Converte a data no formato encontrado no CSV.
df["noted_date"] = pd.to_datetime(
    df["noted_date"],
    format="%d-%m-%Y %H:%M",
    errors="coerce",
)

# Converte a temperatura para número.
df["temperature"] = pd.to_numeric(
    df["temperature"],
    errors="coerce",
)

# Conta e remove registros com campos obrigatórios inválidos.
total_original = len(df)

df = df.dropna(
    subset=[
        "reading_id",
        "device_id",
        "noted_date",
        "temperature",
        "direction",
    ]
).copy()

df["reading_id"] = df["reading_id"].astype(str)
df["device_id"] = df["device_id"].astype(str)
df["direction"] = df["direction"].astype(str)

if df.empty:
    raise ValueError(
        "Nenhum registro válido foi encontrado no CSV."
    )

print(f"Linhas no CSV: {total_original}")
print(f"Registros válidos: {len(df)}")
print(f"Registros ignorados: {total_original - len(df)}")

# Cria a conexão com o PostgreSQL.
engine = create_engine(DATABASE_URL)

# Cria a tabela caso ela ainda não exista.
with engine.begin() as conexao:
    conexao.execute(text("""
        CREATE TABLE IF NOT EXISTS temperature_readings (
            reading_id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            noted_date TIMESTAMP NOT NULL,
            temperature DOUBLE PRECISION NOT NULL,
            direction TEXT NOT NULL
        )
    """))

# Cria uma tabela temporária de preparação dos dados.
# Ela permite importar novamente sem apagar a tabela principal.
df.to_sql(
    "temperature_readings_staging",
    engine,
    if_exists="replace",
    index=False,
)

# Insere apenas os identificadores que ainda não existem.
with engine.begin() as conexao:
    resultado = conexao.execute(text("""
        INSERT INTO temperature_readings (
            reading_id,
            device_id,
            noted_date,
            temperature,
            direction
        )
        SELECT
            reading_id,
            device_id,
            noted_date,
            temperature,
            direction
        FROM temperature_readings_staging
        ON CONFLICT (reading_id) DO NOTHING
    """))

    novos_registros = resultado.rowcount

    conexao.execute(text("""
        DROP TABLE temperature_readings_staging
    """))

# Confere a quantidade total armazenada.
with engine.connect() as conexao:
    total_banco = conexao.execute(
        text("SELECT COUNT(*) FROM temperature_readings")
    ).scalar_one()

print(f"Novos registros inseridos: {novos_registros}")
print(f"Total de registros no banco: {total_banco}")
print("Processamento concluído!")

engine.dispose()
