from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = (
    "postgresql+psycopg2://iot_user:iot_senha_123"
    "@localhost:5433/iot_database"
)

st.set_page_config(
    page_title="Dashboard de Temperatura IoT",
    page_icon="🌡️",
    layout="wide"
)

st.title("Dashboard de Temperatura — IoT")
st.write("Análise das leituras de temperatura dos dispositivos IoT.")

@st.cache_data(ttl=60)
def carregar_dados():
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conexao:
            media_dispositivo = pd.read_sql(
                "SELECT * FROM avg_temp_por_dispositivo",
                conexao
            )

            leituras_hora = pd.read_sql(
                "SELECT * FROM leituras_por_hora",
                conexao
            )

            extremos_dia = pd.read_sql(
                "SELECT * FROM temp_max_min_por_dia ORDER BY data",
                conexao
            )

        return media_dispositivo, leituras_hora, extremos_dia
    finally:
        engine.dispose()

try:
    media_dispositivo, leituras_hora, extremos_dia = carregar_dados()

    st.subheader("1. Temperatura média por dispositivo")
    fig_media = px.bar(
        media_dispositivo,
        x="device_id",
        y="avg_temp",
        labels={
            "device_id": "Dispositivo",
            "avg_temp": "Temperatura média"
        },
        title="Temperatura média registrada por dispositivo"
    )
    st.plotly_chart(fig_media, use_container_width=True)

    st.subheader("2. Quantidade de leituras por hora")
    fig_hora = px.bar(
        leituras_hora,
        x="hora",
        y="contagem",
        labels={
            "hora": "Hora do dia",
            "contagem": "Quantidade de leituras"
        },
        title="Distribuição das leituras ao longo do dia"
    )
    fig_hora.update_xaxes(dtick=1)
    st.plotly_chart(fig_hora, use_container_width=True)

    st.subheader("3. Temperaturas máxima e mínima por dia")
    extremos_dia["data"] = pd.to_datetime(extremos_dia["data"])

    fig_extremos = px.line(
        extremos_dia,
        x="data",
        y=["temp_max", "temp_min"],
        labels={
            "data": "Data",
            "value": "Temperatura",
            "variable": "Medição"
        },
        title="Temperaturas máximas e mínimas diárias"
    )
    st.plotly_chart(fig_extremos, use_container_width=True)

except Exception as erro:
    st.error("Não foi possível carregar os dados do PostgreSQL.")
    st.exception(erro)