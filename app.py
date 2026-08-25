from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from data_utils import (
    FAIXAS_ETARIAS,
    encontrar_coluna,
    percentual_resposta,
    preparar_dados,
    resumo_tcle,
)


BASE_DIR = Path(__file__).resolve().parent
PASTA_DADOS = BASE_DIR / "dados"


st.set_page_config(
    page_title="Dashboard Saúde e Bem-Estar",
    page_icon="🏥",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; font-family: "Inter", sans-serif; }
    [data-testid="stSidebar"] { background-color: #0A0A0F; border-right: 1px solid rgba(255,255,255,0.08); }
    .kpi-card { background: #0A0A0F; min-height: 120px; padding: 20px; border-radius: 16px;
        text-align: center; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px rgba(0,0,0,0.45); }
    .kpi-title { color: rgba(255,255,255,0.65); font-size: 13px; letter-spacing: 0.3px; }
    .kpi-value { font-size: 30px; font-weight: 800; color: #FFFFFF; margin-top: 8px; }
    .kpi-detail { color: rgba(255,255,255,0.55); font-size: 12px; margin-top: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300, show_spinner="Carregando planilhas...")
def carregar_dados(pasta_raiz: str) -> tuple[pd.DataFrame, tuple[str, ...]]:
    arquivos = sorted(
        Path(pasta_raiz).glob("*/resultado_final.xlsx"),
        key=lambda item: item.parent.name.casefold(),
    )
    dataframes: list[pd.DataFrame] = []
    erros: list[str] = []

    for arquivo in arquivos:
        try:
            dados_unidade = pd.read_excel(arquivo, engine="openpyxl")
            dados_unidade.columns = dados_unidade.columns.astype(str).str.strip()
            dados_unidade["Unidade"] = arquivo.parent.name.strip().replace("\u200b", "")
            dataframes.append(dados_unidade)
        except Exception as erro:
            erros.append(f"{arquivo.parent.name}: {erro}")

    if not dataframes:
        return pd.DataFrame(), tuple(erros)
    return pd.concat(dataframes, ignore_index=True), tuple(erros)


def kpi(titulo: str, valor: str | int, detalhe: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-detail">{detalhe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def valor_percentual(percentual: float | None) -> str:
    return "—" if percentual is None else f"{percentual:.1f}%"


st.sidebar.title("Filtros")
if st.sidebar.button("Atualizar dados"):
    carregar_dados.clear()
    st.rerun()

df_bruto, erros = carregar_dados(str(PASTA_DADOS))
if df_bruto.empty:
    st.error("Nenhuma planilha válida foi encontrada em dados/*/resultado_final.xlsx.")
    if erros:
        st.caption(" | ".join(erros))
    st.stop()

df_bruto = preparar_dados(df_bruto)
if erros:
    st.warning("Algumas planilhas não foram carregadas: " + " | ".join(erros))

unidades = sorted(df_bruto["Unidade"].dropna().unique(), key=str.casefold)
unidades_selecionadas = st.sidebar.multiselect("Unidades", options=unidades, default=unidades)
df = df_bruto.loc[df_bruto["Unidade"].isin(unidades_selecionadas)].copy()

st.sidebar.metric("Registros carregados", len(df_bruto))
st.sidebar.metric("Após filtro", len(df))

st.title("🏥 Dashboard Saúde e Bem-Estar")
st.caption(
    "Participação e perfil demográfico das respostas coletadas. "
    "Dados individuais identificáveis não são exibidos."
)

if df.empty:
    st.info("Selecione pelo menos uma unidade para visualizar os indicadores.")
    st.stop()

confirmados_tcle, respondidos_tcle = resumo_tcle(df)
idade_valida = df["Idade"].dropna()
idade_media = "—" if idade_valida.empty else f"{idade_valida.mean():.1f} anos"
percentual_mulheres, base_sexo = percentual_resposta(df, "Demografico.sexo", "Feminino")
percentual_homens, _ = percentual_resposta(df, "Demografico.sexo", "Masculino")
percentual_sozinhos, base_mora_sozinho = percentual_resposta(
    df, "Demografico.moraSozinho", "Sim"
)

colunas_kpi = st.columns(6)
with colunas_kpi[0]:
    kpi("Registros", len(df), "após filtro")
with colunas_kpi[1]:
    kpi("TCLE confirmado", confirmados_tcle, f"{respondidos_tcle} respostas válidas")
with colunas_kpi[2]:
    kpi("Idade média", idade_media, f"base de {len(idade_valida)} registros")
with colunas_kpi[3]:
    kpi("% Mulheres", valor_percentual(percentual_mulheres), f"base de {base_sexo} respostas")
with colunas_kpi[4]:
    kpi("% Homens", valor_percentual(percentual_homens), f"base de {base_sexo} respostas")
with colunas_kpi[5]:
    kpi(
        "% Mora sozinho",
        valor_percentual(percentual_sozinhos),
        f"base de {base_mora_sozinho} respostas",
    )

st.divider()
grafico_faixa, grafico_sexo = st.columns(2)

with grafico_faixa:
    faixa_df = (
        df["Faixa etária"]
        .value_counts()
        .reindex(FAIXAS_ETARIAS, fill_value=0)
        .rename_axis("Faixa etária")
        .reset_index(name="Quantidade")
    )
    figura_faixa = px.bar(
        faixa_df,
        x="Faixa etária",
        y="Quantidade",
        text="Quantidade",
        category_orders={"Faixa etária": FAIXAS_ETARIAS},
        title="Distribuição por faixa etária",
        template="plotly_dark",
        color_discrete_sequence=["#6C5CE7"],
    )
    figura_faixa.update_layout(paper_bgcolor="#000000", plot_bgcolor="#0A0A0F")
    st.plotly_chart(figura_faixa, width="stretch")

with grafico_sexo:
    coluna_sexo = encontrar_coluna(df.columns, "Demografico.sexo")
    if coluna_sexo:
        sexo_df = df[coluna_sexo].fillna("Não informado").astype(str).str.strip()
        figura_sexo = px.pie(
            names=sexo_df,
            hole=0.55,
            title="Sexo",
            template="plotly_dark",
            color_discrete_sequence=["#6C5CE7", "#00CEC9", "#636E72"],
        )
        figura_sexo.update_layout(paper_bgcolor="#000000", legend_title_text="")
        st.plotly_chart(figura_sexo, width="stretch")
    else:
        st.info("A coluna de sexo não está disponível nos dados selecionados.")

st.subheader("Dados anonimizados")
coluna_sexo = encontrar_coluna(df.columns, "Demografico.sexo")
coluna_mora_sozinho = encontrar_coluna(df.columns, "Demografico.moraSozinho")
tabela_segura = pd.DataFrame(
    {
        "Unidade": df["Unidade"],
        "Faixa etária": df["Faixa etária"],
        "Origem da idade": df["Origem da idade"],
        "Sexo": df[coluna_sexo] if coluna_sexo else "Não informado",
        "Mora sozinho": df[coluna_mora_sozinho] if coluna_mora_sozinho else "Não informado",
    }
)
st.dataframe(tabela_segura, width="stretch", height=500, hide_index=True)
st.caption(
    "Idade derivada de data de nascimento quando disponível; quando há somente o ano, "
    "a idade é estimada e pode variar em um ano."
)
