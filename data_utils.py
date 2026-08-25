"""Funções puras para preparar os dados do dashboard."""

from __future__ import annotations

from datetime import date
from numbers import Real
import re
import unicodedata

import pandas as pd


MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

FAIXAS_ETARIAS = ["<50", "50-59", "60-69", "70-79", "80+", "Não informado"]


def normalizar_texto(valor: object) -> str:
    """Normaliza respostas para comparações, inclusive valores com acentos corrompidos."""
    if pd.isna(valor):
        return ""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, Real) and valor in {0, 1}:
        return str(int(valor))

    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", texto.lower())


def encontrar_coluna(colunas: pd.Index, final_nome: str) -> str | None:
    """Encontra uma coluna pelo sufixo, sem depender de estado global."""
    final_normalizado = final_nome.lower()
    return next(
        (
            coluna
            for coluna in colunas
            if str(coluna).lower().endswith(final_normalizado)
        ),
        None,
    )


def converter_data_nascimento(valor: object, referencia: pd.Timestamp) -> pd.Timestamp:
    """Converte datas brasileiras completas, incluindo meses por extenso."""
    if pd.isna(valor):
        return pd.NaT

    if isinstance(valor, (pd.Timestamp, date)):
        data = pd.Timestamp(valor)
    else:
        texto = str(valor).strip()
        texto_sem_acentos = unicodedata.normalize("NFKD", texto).encode(
            "ascii", "ignore"
        ).decode().lower()
        match_numerico = re.fullmatch(r"(\d{2})(\d{2})(\d{4})", texto_sem_acentos)
        match_semi_numerico = re.fullmatch(r"(\d{1,2})\s+(\d{2})(\d{4})", texto_sem_acentos)
        match_data_curta = re.fullmatch(
            r"(\d{1,2})[./\s]+(\d{1,2})[./\s]+(\d{2,4})", texto_sem_acentos
        )
        match_extenso = re.fullmatch(
            r"(\d{1,2})\s+(?:de\s+)?([a-z]+)(?:\s+de)?\s*-?\s*(\d{4})",
            texto_sem_acentos,
        )

        if match_numerico or match_semi_numerico or match_data_curta:
            dia, mes, ano = map(
                int, (match_numerico or match_semi_numerico or match_data_curta).groups()
            )
            if match_data_curta and mes > 12 and dia <= 12:
                dia, mes = mes, dia
            if ano < 100:
                ano = 2000 + ano
                if ano > referencia.year:
                    ano -= 100
            data = pd.to_datetime(
                f"{dia:02d}/{mes:02d}/{ano}", format="%d/%m/%Y", errors="coerce"
            )
        elif match_extenso and match_extenso.group(2) in MESES:
            dia = int(match_extenso.group(1))
            mes = MESES[match_extenso.group(2)]
            ano = int(match_extenso.group(3))
            data = pd.to_datetime(
                f"{dia:02d}/{mes:02d}/{ano}", format="%d/%m/%Y", errors="coerce"
            )
        else:
            data = pd.to_datetime(texto, format="mixed", dayfirst=True, errors="coerce")
            if pd.isna(data):
                data = pd.to_datetime(texto, format="mixed", dayfirst=False, errors="coerce")

    if pd.isna(data) or data.year < 1900 or data > referencia:
        return pd.NaT
    return pd.Timestamp(data)


def faixa_etaria(idade: float | int | None) -> str:
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


def preparar_dados(df: pd.DataFrame, referencia: pd.Timestamp | None = None) -> pd.DataFrame:
    """Cria idade e faixa etária usando data completa ou ano, nessa ordem."""
    resultado = df.copy()
    referencia = pd.Timestamp(referencia or pd.Timestamp.today()).normalize()
    coluna_data = encontrar_coluna(resultado.columns, "Demografico.dataNascimento")
    coluna_ano = encontrar_coluna(resultado.columns, "Demografico.anoNascimento")

    if coluna_data:
        nascimento = resultado[coluna_data].map(
            lambda valor: converter_data_nascimento(valor, referencia)
        )
    else:
        nascimento = pd.Series(pd.NaT, index=resultado.index, dtype="datetime64[us]")

    idade_por_data = pd.Series(pd.NA, index=resultado.index, dtype="Int64")
    tem_data = nascimento.notna()
    idade_por_data.loc[tem_data] = (
        referencia.year
        - nascimento.loc[tem_data].dt.year
        - (
            (referencia.month < nascimento.loc[tem_data].dt.month)
            | (
                (referencia.month == nascimento.loc[tem_data].dt.month)
                & (referencia.day < nascimento.loc[tem_data].dt.day)
            )
        ).astype(int)
    ).astype("Int64")

    idade_por_ano = pd.Series(pd.NA, index=resultado.index, dtype="Int64")
    if coluna_ano:
        anos = pd.to_numeric(resultado[coluna_ano], errors="coerce")
        anos_validos = anos.notna() & anos.eq(anos.round()) & anos.between(1900, referencia.year)
        idade_por_ano.loc[anos_validos] = (referencia.year - anos.loc[anos_validos]).astype("Int64")

    resultado["Idade"] = idade_por_data.combine_first(idade_por_ano)
    resultado["Origem da idade"] = "Não informado"
    resultado.loc[idade_por_ano.notna(), "Origem da idade"] = "Ano de nascimento"
    resultado.loc[idade_por_data.notna(), "Origem da idade"] = "Data de nascimento"
    resultado["Faixa etária"] = resultado["Idade"].map(faixa_etaria)
    return resultado


def percentual_resposta(df: pd.DataFrame, final_coluna: str, valor: str) -> tuple[float | None, int]:
    """Retorna percentual sobre respostas preenchidas e o tamanho da base."""
    coluna = encontrar_coluna(df.columns, final_coluna)
    if coluna is None:
        return None, 0

    respostas = df[coluna].map(normalizar_texto)
    respondidos = respostas[respostas.ne("")]
    if respondidos.empty:
        return None, 0
    return round(respondidos.eq(normalizar_texto(valor)).mean() * 100, 1), len(respondidos)


def resumo_tcle(df: pd.DataFrame) -> tuple[int, int]:
    """Retorna confirmações TCLE e respostas válidas dessa pergunta."""
    coluna = encontrar_coluna(df.columns, "participanteTCLE")
    if coluna is None:
        return 0, 0

    respostas = df[coluna].map(normalizar_texto)
    valores_verdadeiros = {"true", "1", "sim", "s", "yes", "y", "verdadeiro"}
    valores_falsos = {"false", "0", "nao", "no", "n", "f", "falso"}
    respondidos = respostas.isin(valores_verdadeiros | valores_falsos)
    confirmados = respostas.isin(valores_verdadeiros).sum()
    return int(confirmados), int(respondidos.sum())
