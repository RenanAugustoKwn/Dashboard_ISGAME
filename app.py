import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Dashboard Saúde e Bem-Estar",
    page_icon="🏥",
    layout="wide"
)

# =====================================================
# CSS MODERNO (FORÇADO DARK PRETO)
# =====================================================

st.markdown("""
<style>

/* Fundo geral preto */
.stApp {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    font-family: "Inter", sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0A0A0F !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Cards KPI */
.kpi-card {
    background: #0A0A0F;
    padding: 22px;
    border-radius: 16px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 30px rgba(0,0,0,0.45);
    transition: all 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-4px);
    border-color: #6C5CE7;
}

.kpi-title {
    color: rgba(255,255,255,0.6);
    font-size: 13px;
    letter-spacing: 0.3px;
}

.kpi-value {
    font-size: 34px;
    font-weight: 800;
    color: #FFFFFF;
}

/* Títulos gerais */
h1, h2, h3 {
    color: #FFFFFF !important;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    background-color: #0A0A0F;
    border-radius: 12px;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DADOS
# =====================================================

@st.cache_data
def carregar_dados():

    pasta_raiz = Path("dados")

    arquivos = list(pasta_raiz.glob("*/resultado_final.xlsx"))

    dfs = []

    for arquivo in arquivos:

        try:
            df = pd.read_excel(arquivo, engine="openpyxl")

            df.columns = (
                df.columns
                .astype(str)
                .str.strip()
            )

            # Unidade (nome da pasta)
            df["Unidade"] = arquivo.parent.name

            dfs.append(df)

        except Exception as e:
            st.warning(f"Erro ao carregar {arquivo}: {e}")

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


df = carregar_dados()
# =====================================================
# DIAGNÓSTICO
# =====================================================

st.success(
    f"Registros carregados: {len(df)}"
)


# =====================================================
# HEADER
# =====================================================

st.title("🏥 Dashboard Saúde e Bem-Estar")

st.caption(
    "Indicadores de Qualidade de Vida, Saúde Física, Memória e Humor"
)
# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def encontrar_coluna(final_nome):
    """
    Procura uma coluna pelo final do nome,
    ignorando maiúsculas/minúsculas.

    Exemplo:
        respostasDemografico.sexo
        respostasDemografico.dataNascimento
        respostasHumor.felicidade
    """

    final_nome = final_nome.lower()

    for coluna in df.columns:
        if coluna.lower().endswith(final_nome):
            return coluna

    return None


def percentual(final_coluna, valor):

    coluna = encontrar_coluna(final_coluna)

    if coluna is None:
        return 0.0

    serie = (
        df[coluna]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return round(
        serie.eq(str(valor).strip().lower()).mean() * 100,
        1
    )


def kpi(titulo, valor):

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# IDADE
# =====================================================

col_nascimento = (
    encontrar_coluna("Demografico.dataNascimento")
    or encontrar_coluna("Demografico.anoNascimento")
)

if col_nascimento:

    nascimento = pd.to_datetime(
        df[col_nascimento],
        errors="coerce",
        dayfirst=True
    )

    hoje = pd.Timestamp.today()

    df["Idade"] = (
        hoje.year
        - nascimento.dt.year
        - (
            (hoje.month < nascimento.dt.month)
            | (
                (hoje.month == nascimento.dt.month)
                & (hoje.day < nascimento.dt.day)
            )
        ).astype(int)
    )

else:

    df["Idade"] = np.nan


def faixa_etaria(idade):

    if pd.isna(idade):
        return "Não informado"

    if idade < 50:
        return "<50"
    elif idade < 60:
        return "50-59"
    elif idade < 70:
        return "60-69"
    elif idade < 80:
        return "70-79"
    else:
        return "80+"


df["FaixaEtaria"] = df["Idade"].apply(faixa_etaria)
# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

total_original = len(df)

if "Unidade" not in df.columns:
    df["Unidade"] = "Sem Unidade"

df["Unidade"] = (
    df["Unidade"]
    .fillna("Sem Unidade")
    .astype(str)
    .str.strip()
)

df.loc[
    df["Unidade"].isin([
        "",
        "nan",
        "None",
        "N/A"
    ]),
    "Unidade"
] = "Sem Unidade"

unidades = sorted(df["Unidade"].unique())

unidades_selecionadas = st.sidebar.multiselect(
    "Unidades",
    options=unidades,
    default=unidades
)

df = df[
    df["Unidade"].isin(unidades_selecionadas)
]

st.sidebar.metric(
    "Total de Registros",
    total_original
)

st.sidebar.metric(
    "Após Filtro",
    len(df)
)

# =====================================================
# COLUNAS ENCONTRADAS (DEBUG)
# =====================================================

COL_SEXO = encontrar_coluna("sexo")
COL_MORA_SOZINHO = encontrar_coluna("moraSozinho")
COL_TCLE = encontrar_coluna("participanteTCLE")
COL_NASCIMENTO = (
    encontrar_coluna("dataNascimento")
    or encontrar_coluna("anoNascimento")
)
# =====================================================
# PARTICIPANTES TCLE
# =====================================================

participantes_tcle = 0

col_tcle = encontrar_coluna("participanteTCLE")

if col_tcle:

    participantes_tcle = (
        df[col_tcle]
        .fillna(False)              # NaN -> False
        .replace({
            True: "true",
            False: "false",
            1: "true",
            0: "false",
            1.0: "true",
            0.0: "false",
        })
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({
            "1": "true",
            "0": "false",
            "sim": "true",
            "não": "false",
            "nao": "false",
            "yes": "true",
            "no": "false",
            "y": "true",
            "n": "false",
            "s": "true",
            "f": "false",
            "verdadeiro": "true",
            "falso": "false",
            "none": "false",
            "nan": "false",
            "": "false"
        })
        .eq("true")
        .sum()
    )
# =====================================================
# IDADE MÉDIA
# =====================================================

idade_media = "-"

col_nascimento = encontrar_coluna("Demografico.anoNascimento")

if col_nascimento:

    df["Idade"] = (
        datetime.now().year -
        pd.to_numeric(
            df[col_nascimento],
            errors="coerce"
        )
    )

    idade_media = round(df["Idade"].mean(), 1)

# =====================================================
# KPIs
# =====================================================

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    kpi("Total Participantes TCLE", participantes_tcle)

with col2:
    kpi("Registros", len(df))

with col3:
    kpi("Idade Média", idade_media)

with col4:
    kpi(
        "% Mulheres",
        f"{percentual('Demografico.sexo', 'Feminino')}%"
    )

with col5:
    kpi(
        "% Homens",
        f"{percentual('Demografico.sexo', 'Masculino')}%"
    )

with col6:
    kpi(
        "% Mora Sozinho",
        f"{percentual('Demografico.moraSozinho', 'Sim')}%"
    )

st.divider()
# =====================================================
# DEMOGRÁFICO
# =====================================================

c1, c2 = st.columns(2)

with c1:

    faixa_df = (
        df["FaixaEtaria"]
        .dropna()
        .value_counts()
        .rename_axis("Faixa")
        .reset_index(name="Quantidade")
    )

    fig = px.bar(
        faixa_df,
        x="Faixa",
        y="Quantidade",
        text="Quantidade",
        title="Distribuição por Faixa Etária"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with c2:

    if "respostasDemografico.sexo" in df.columns:

        fig = px.pie(
            df,
            names="respostasDemografico.sexo",
            hole=.55,
            title="Sexo"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# TABELA
# =====================================================

st.subheader("Dados")

st.dataframe(
    df,
    use_container_width=True,
    height=700
)

# =====================================================
# FOOTER
# =====================================================

st.caption(
    f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)