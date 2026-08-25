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
NAO_INFORMADO = "Não informado"

# O mapeamento usa os mesmos campos do arquivo de exportação fornecido.
BLOCOS = {
    "Demográfico": {
        "prefixo": "respostasDemografico.",
        "campos": {
            "estadoCivil": "Estado civil",
            "sexo": "Sexo",
            "moraSozinho": "Mora sozinho",
            "escolaridade": "Escolaridade",
            "renda": "Renda",
            "etnia": "Etnia",
            "trabalho": "Trabalha atualmente",
            "possuiReligiao": "Possui religião",
        },
    },
    "Nutrição": {
        "prefixo": "respostasNutricao.",
        "campos": {
            "comeVerduras": "Consome verduras",
            "comeGordura": "Consome alimentos gordurosos",
            "fazQuatroRefeicoes": "Faz quatro refeições por dia",
        },
    },
    "Atividade física": {
        "prefixo": "respostasAtividadeFisica.",
        "campos": {
            "fazExercicios": "Pratica exercícios",
            "fazExerciciosForca": "Pratica exercícios de força",
            "fazCaminhada": "Faz caminhada",
        },
    },
    "Comportamento preventivo": {
        "prefixo": "respostasComportamentoPreventivo.",
        "campos": {
            "conhecePressaoColesterol": "Conhece pressão arterial e colesterol",
            "fuma": "Fuma",
            "ingereBebidaAlcoolica": "Consome bebida alcoólica",
            "respeitaTransito": "Respeita as regras de trânsito",
        },
    },
    "Relacionamento": {
        "prefixo": "respostasRelacionamento.",
        "campos": {
            "cultivaAmigos": "Cultiva amizades",
            "lazerAmigos": "Tem lazer com amigos",
            "ativoComunidade": "É ativo na comunidade",
        },
    },
    "Controle do estresse": {
        "prefixo": "respostasControleEstresse.",
        "campos": {
            "reservaTempoRelaxar": "Reserva tempo para relaxar",
            "calmaDiscussao": "Mantém a calma em discussões",
            "dedicaTempoLazer": "Dedica tempo ao lazer",
        },
    },
    "Sono e água": {
        "prefixo": "respostasSonoAgua.",
        "campos": {
            "horasSono": "Horas de sono habituais",
            "tiraCochilos": "Tira cochilos",
            "cochiloPeriodo": "Período do cochilo",
            "horasSonoNoitePassada": "Horas de sono na noite anterior",
            "coposAguaOntem": "Copos de água no dia anterior",
        },
    },
    "Saúde": {
        "prefixo": "respostasSaude.",
        "campos": {
            "idaMedico": "Tempo desde a última ida ao médico",
            "avaliacaoSaude": "Avaliação da saúde atual",
            "avaliacaoSaudeUmAnoAtras": "Avaliação da saúde há um ano",
            "avaliacaoSaudeOutrasPessoas": "Avaliação da saúde por outras pessoas",
            "temDoenca": "Possui alguma doença",
            "temDiabete": "Possui diabetes",
            "temPressaoAlta": "Possui pressão alta",
            "temDoencaCardiaca": "Possui doença cardíaca",
            "temColesterolAlto": "Possui colesterol alto",
            "acompanhaSaude": "Acompanha a própria saúde",
            "servicosUtiliza": "Serviço de saúde utilizado",
            "usaMedicamentos": "Usa medicamentos",
            "quantidadeMedicamentos": "Quantidade de medicamentos",
            "medicamentos": "Medicamentos informados",
            "alergias": "Alergias informadas",
            "alzheimerFamilia": "Histórico familiar de Alzheimer",
        },
    },
    "Memória": {
        "prefixo": "respostasMemoria.",
        "campos": {
            "lembraCompromisso": "Lembra compromissos",
            "usaAgenda": "Usa agenda",
            "deixaBilhete": "Deixa bilhetes",
            "repeteHistoria": "Repete histórias",
            "passaRecado": "Consegue passar recados",
            "esqueceMercado": "Esquece itens no mercado",
            "esqueceObjetos": "Esquece onde colocou objetos",
            "esqueceArtistas": "Esquece nomes de artistas",
            "avaliacaoMemoria": "Avaliação da memória atual",
            "avaliacaoMemoriaOutrasPessoas": "Avaliação da memória por outras pessoas",
            "avaliacaoMemoriaUmAnoAtras": "Avaliação da memória há um ano",
        },
    },
    "Humor": {
        "prefixo": "respostasHumor.",
        "campos": {
            "satisfacaoVida": "Satisfação com a vida",
            "sentidoVida": "Sente que a vida tem sentido",
            "inseguranca": "Sente insegurança",
            "felicidade": "Sente-se feliz",
        },
    },
}

COLUNAS_PRIVADAS = {
    "Unnamed: 0",
    "username",
    "nome",
    "email",
    "numeroRegistroProfissional",
    "respostasDemografico.dataNascimento",
    "respostasDemografico.anoNascimento",
}
COLUNAS_TECNICAS = {"respostasMemoria", "respostasHumor", "respostasSaude"}


st.set_page_config(page_title="Dashboard Saúde e Bem-Estar", page_icon="🏥", layout="wide")

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
    return (
        (pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()),
        tuple(erros),
    )


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


def contagem_respostas(serie: pd.Series) -> pd.DataFrame:
    respostas = serie.fillna(NAO_INFORMADO).astype(str).str.strip().replace("", NAO_INFORMADO)
    return respostas.value_counts().rename_axis("Resposta").reset_index(name="Quantidade")


def titulo_coluna(coluna: str) -> str:
    nomes = {
        "Unidade": "Unidade",
        "participantePesquisa": "Participante da pesquisa",
        "participanteTCLE": "Participante TCLE",
        "Idade": "Idade",
        "Faixa etária": "Faixa etária",
        "Origem da idade": "Origem da idade",
    }
    if coluna in nomes:
        return nomes[coluna]
    for bloco, configuracao in BLOCOS.items():
        prefixo = configuracao["prefixo"]
        if coluna == f"{prefixo}dataResposta":
            return f"Data da resposta — {bloco}"
        for campo, titulo in configuracao["campos"].items():
            if coluna == f"{prefixo}{campo}":
                return f"{bloco} — {titulo}"
    return coluna


def dados_detalhados(df: pd.DataFrame) -> pd.DataFrame:
    preferidas = ["Unidade", "Idade", "Faixa etária", "Origem da idade", "participantePesquisa", "participanteTCLE"]
    disponiveis = [coluna for coluna in preferidas if coluna in df.columns]
    demais = [
        coluna
        for coluna in df.columns
        if coluna not in set(disponiveis) | COLUNAS_PRIVADAS | COLUNAS_TECNICAS
    ]
    resultado = df[disponiveis + demais].copy()
    for coluna in resultado.columns:
        serie = resultado[coluna]
        if pd.api.types.is_object_dtype(serie) or isinstance(serie.dtype, pd.StringDtype):
            resultado[coluna] = serie.astype("string").fillna(NAO_INFORMADO)
    return resultado.rename(columns={coluna: titulo_coluna(coluna) for coluna in resultado.columns})


def exibir_bloco(df: pd.DataFrame, nome_bloco: str, configuracao: dict[str, object]) -> None:
    campos = configuracao["campos"]
    prefixo = configuracao["prefixo"]
    campo = st.selectbox(
        "Pergunta",
        options=list(campos),
        format_func=lambda chave: campos[chave],
        key=f"pergunta-{nome_bloco}",
    )
    coluna = encontrar_coluna(df.columns, f"{prefixo}{campo}")
    if coluna is None:
        st.warning("Este campo não está disponível nas planilhas selecionadas.")
        return

    contagem = contagem_respostas(df[coluna])
    respondidos = len(df) - int(contagem.loc[contagem["Resposta"].eq(NAO_INFORMADO), "Quantidade"].sum())
    grafico, tabela = st.columns((2, 1))
    with grafico:
        figura = px.bar(
            contagem,
            x="Quantidade",
            y="Resposta",
            orientation="h",
            text="Quantidade",
            title=campos[campo],
            template="plotly_dark",
            color_discrete_sequence=["#6C5CE7"],
        )
        figura.update_layout(
            paper_bgcolor="#000000",
            plot_bgcolor="#0A0A0F",
            yaxis={"categoryorder": "total ascending"},
            margin={"l": 10, "r": 10, "t": 60, "b": 10},
        )
        st.plotly_chart(figura, width="stretch")
    with tabela:
        st.metric("Respostas preenchidas", respondidos, f"de {len(df)} registros")
        st.dataframe(contagem, width="stretch", hide_index=True, height=360)


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
st.caption("Indicadores de todos os blocos do questionário. Identificadores diretos — nome, e-mail, usuário e registro profissional — não são exibidos.")

if df.empty:
    st.info("Selecione pelo menos uma unidade para visualizar os indicadores.")
    st.stop()

confirmados_tcle, respondidos_tcle = resumo_tcle(df)
idade_valida = df["Idade"].dropna()
idade_media = "—" if idade_valida.empty else f"{idade_valida.mean():.1f} anos"
percentual_mulheres, base_sexo = percentual_resposta(df, "Demografico.sexo", "Feminino")
percentual_homens, _ = percentual_resposta(df, "Demografico.sexo", "Masculino")
percentual_sozinhos, base_mora_sozinho = percentual_resposta(df, "Demografico.moraSozinho", "Sim")

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
    kpi("% Mora sozinho", valor_percentual(percentual_sozinhos), f"base de {base_mora_sozinho} respostas")

abas = st.tabs(["Visão geral", *BLOCOS.keys(), "Dados completos"])

with abas[0]:
    faixa_df = (
        df["Faixa etária"]
        .value_counts()
        .reindex(FAIXAS_ETARIAS, fill_value=0)
        .rename_axis("Faixa etária")
        .reset_index(name="Quantidade")
    )
    coluna_sexo = encontrar_coluna(df.columns, "Demografico.sexo")
    grafico_faixa, grafico_sexo = st.columns(2)
    with grafico_faixa:
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
        if coluna_sexo:
            figura_sexo = px.pie(
                names=df[coluna_sexo].fillna(NAO_INFORMADO).astype(str).str.strip(),
                hole=0.55,
                title="Sexo",
                template="plotly_dark",
                color_discrete_sequence=["#6C5CE7", "#00CEC9", "#636E72"],
            )
            figura_sexo.update_layout(paper_bgcolor="#000000", legend_title_text="")
            st.plotly_chart(figura_sexo, width="stretch")
        else:
            st.info("A coluna de sexo não está disponível nos dados selecionados.")
    st.info("Use as abas para analisar cada dimensão e escolha uma pergunta para ver a distribuição completa das respostas.")

for indice, (nome_bloco, configuracao) in enumerate(BLOCOS.items(), start=1):
    with abas[indice]:
        exibir_bloco(df, nome_bloco, configuracao)

with abas[-1]:
    tabela_completa = dados_detalhados(df)
    st.subheader("Dados completos anonimizados")
    st.caption("Inclui todos os campos do questionário de referência, exceto identificadores diretos e as datas/anos de nascimento — substituídos por idade e faixa etária.")
    st.download_button(
        "Baixar dados anonimizados (CSV)",
        data=tabela_completa.to_csv(index=False).encode("utf-8-sig"),
        file_name="dashboard_isgame_anonimizado.csv",
        mime="text/csv",
    )
    st.dataframe(tabela_completa, width="stretch", height=650, hide_index=True)
