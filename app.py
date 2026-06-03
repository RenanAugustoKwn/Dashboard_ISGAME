import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Dashboard Saúde e Bem-Estar",
    page_icon="🏥",
    layout="wide"
)

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>
.stApp {
    background-color: #0A0A0F;
}

[data-testid="stSidebar"] {
    background-color: #171721;
}

.kpi-card{
    background:#171721;
    padding:20px;
    border-radius:16px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.08);
}

.kpi-title{
    color:#FFFFFF;
    font-size:14px;
}

.kpi-value{
    font-size:30px;
    font-weight:bold;
    color:white;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# DADOS
# =====================================================

@st.cache_data
def carregar_dados():

    df = pd.read_excel(
        "Resultados_Pesquisas.xlsx",
        engine="openpyxl"
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


df = carregar_dados()

# =====================================================
# DIAGNÓSTICO
# =====================================================

st.success(
    f"Registros carregados: {len(df)}"
)

# =====================================================
# IDADE
# =====================================================

ano_atual = datetime.now().year

if "Demografico.anoNascimento" in df.columns:

    df["Idade"] = (
        ano_atual -
        pd.to_numeric(
            df["Demografico.anoNascimento"],
            errors="coerce"
        )
    )

elif "Demografico_Nascimento" in df.columns:

    df["Idade"] = (
        ano_atual -
        pd.to_numeric(
            df["Demografico_Nascimento"],
            errors="coerce"
        )
    )

else:
    df["Idade"] = np.nan


def faixa_etaria(idade):

    if pd.isna(idade):
        return "Não informado"

    if idade < 50:
        return "<50"

    if idade < 60:
        return "50-59"

    if idade < 70:
        return "60-69"

    if idade < 80:
        return "70-79"

    return "80+"


df["FaixaEtaria"] = df["Idade"].apply(faixa_etaria)

# =====================================================
# HEADER
# =====================================================

st.title("🏥 Dashboard Saúde e Bem-Estar")

st.caption(
    "Indicadores de Qualidade de Vida, Saúde Física, Memória e Humor"
)

# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

total_original = len(df)

if "Unidade" in df.columns:

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

    unidades = sorted(
        df["Unidade"]
        .unique()
        .tolist()
    )

    unidades_selecionadas = st.sidebar.multiselect(
        "Unidades",
        options=unidades,
        default=unidades
    )

    df = df[
        df["Unidade"]
        .isin(unidades_selecionadas)
    ]

st.sidebar.metric(
    "Total Excel",
    total_original
)

st.sidebar.metric(
    "Após filtros",
    len(df)
)

# =====================================================
# KPIS
# =====================================================

def percentual(coluna, valor):

    if coluna not in df.columns:
        return 0

    return round(
        (
            df[coluna]
            .astype(str)
            .str.strip()
            .eq(valor)
            .mean()
        ) * 100,
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


col1,col2,col3,col4,col5 = st.columns(5)

with col1:
    kpi("Participantes", len(df))

with col2:
    kpi(
        "Idade Média",
        round(df["Idade"].mean(),1)
    )

with col3:
    kpi(
        "% Mulheres",
        f"{percentual('Demografico_Sexo','Feminino')}%"
    )

with col4:
    kpi(
        "% Homens",
        f"{percentual('Demografico_Sexo','Masculino')}%"
    )

with col5:
    kpi(
        "% Mora Sozinho",
        f"{percentual('Pergunta: Mora_Sozinho','Sim')}%"
    )

st.divider()

# =====================================================
# DEMOGRÁFICO
# =====================================================

c1,c2 = st.columns(2)

with c1:

    faixa_df = (
        df["FaixaEtaria"]
        .value_counts()
        .reset_index()
    )

    faixa_df.columns = [
        "Faixa",
        "Quantidade"
    ]

    fig = px.bar(
        faixa_df,
        x="Faixa",
        y="Quantidade",
        title="Distribuição por Faixa Etária"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with c2:

    if "Demografico_Sexo" in df.columns:

        fig = px.pie(
            df,
            names="Demografico_Sexo",
            hole=.55,
            title="Sexo"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# BEM ESTAR
# =====================================================

st.subheader("Índice Geral de Bem-Estar")

bem_estar = percentual(
    "Estrela do Bem-estar",
    "Sim"
)

fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=bem_estar,
        title={"text":"Bem-estar (%)"}
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# RADAR
# =====================================================

MAP = {
    "Sempre":100,
    "Sim":100,
    "Excelente":100,
    "Boa":75,
    "Regular":50,
    "Às vezes":50,
    "Não":0,
    "Nunca":0
}


def score(col):

    if col not in df.columns:
        return 0

    serie = (
        df[col]
        .astype(str)
        .str.strip()
        .map(MAP)
    )

    return (
        float(serie.mean())
        if serie.notna().any()
        else 0
    )


st.subheader("Radar de Qualidade de Vida")

radar = {
    "Nutrição": np.nanmean([
        score("Nutricao_ComeVerduras"),
        score("Nutricao_FazQuatroRefeicoes")
    ]),
    "Atividade Física": np.nanmean([
        score("AtividadeFisicaFaz_Exercicios"),
        score("AtividadeFisica_FazCaminhada")
    ]),
    "Relacionamentos": score(
        "Relacionamento_CultivaAmigos"
    ),
    "Estresse": score(
        "ControleEstresse_ReservaTempoRelaxar"
    ),
    "Saúde": score(
        "Saude_AavaliacaoSaude"
    ),
    "Memória": score(
        "Memoria_LembraCompromisso"
    ),
    "Humor": score(
        "Humor_Felicidade"
    )
}

categorias = list(radar.keys())
valores = list(radar.values())

categorias.append(categorias[0])
valores.append(valores[0])

fig = go.Figure()

fig.add_trace(
    go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill="toself"
    )
)

fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0,100]
        )
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# HÁBITOS
# =====================================================

st.subheader("Hábitos Saudáveis")

c1,c2 = st.columns(2)

with c1:

    if "Nutricao_ComeVerduras" in df.columns:

        fig = px.histogram(
            df,
            x="Nutricao_ComeVerduras",
            title="Consumo de Verduras"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

with c2:

    if "Nutricao_ComeGordura" in df.columns:

        fig = px.histogram(
            df,
            x="Nutricao_ComeGordura",
            title="Consumo de Gordura"
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