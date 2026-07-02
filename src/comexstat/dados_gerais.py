from __future__ import annotations

from typing import Any

import pandas as pd

from comexstat.client import post_json


DETAILS_DADOS_GERAIS = ["state", "ISICDivision", "ncm", "country"]
METRICS_DADOS_GERAIS = ["metricFOB", "metricKG", "metricStatistic"]

COLUMN_RENAMES = {
    "coIsicDivision": "isic_divisao_codigo",
    "ISICDivision": "isic_divisao_descricao",
    "coNcm": "ncm_codigo",
    "ncm": "ncm_descricao",
    "year": "ano",
    "monthNumber": "mes_num",
    "state": "uf_produto",
    "country": "pais",
    "metricFOB": "valor_usd_fob",
    "metricKG": "kg_liquido",
    "metricStatistic": "quantidade_estatistica",
}

FINAL_COLUMN_ORDER = [
    "fluxo",
    "ano",
    "mes_num",
    "uf_produto",
    "isic_divisao_codigo",
    "isic_divisao_descricao",
    "ncm_codigo",
    "ncm_descricao",
    "pais",
    "valor_usd_fob",
    "kg_liquido",
    "quantidade_estatistica",
]


def montar_payload_dados_gerais(
    fluxo: str,
    data_inicio: str,
    data_fim: str,
    detalhes: list[str],
    metricas: list[str],
    filtros: list[dict[str, Any]] | None = None,
    detalhar_mes: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "flow": fluxo,
        "monthDetail": detalhar_mes,
        "period": {
            "from": data_inicio,
            "to": data_fim,
        },
        "details": detalhes,
        "metrics": metricas,
    }

    if filtros:
        payload["filters"] = filtros

    return payload


def montar_payload_fluxo_uf_mes(
    fluxo: str,
    uf_codigo: str,
    data_inicio: str,
    data_fim: str,
) -> dict[str, Any]:
    return montar_payload_dados_gerais(
        fluxo=fluxo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        detalhes=DETAILS_DADOS_GERAIS,
        metricas=METRICS_DADOS_GERAIS,
        filtros=[{"filter": "state", "values": [str(uf_codigo)]}],
        detalhar_mes=True,
    )


def consultar_dados_gerais(payload: dict[str, Any]) -> dict[str, Any]:
    return post_json("/general", payload=payload)


def normalizar_resposta_dados_gerais(resposta: dict[str, Any]) -> pd.DataFrame:
    data = resposta.get("data")
    if not isinstance(data, dict):
        chaves = sorted(resposta.keys())
        print(f"Chaves disponiveis no topo da resposta: {chaves}")
        raise ValueError(
            "Estrutura inesperada na resposta de /general: "
            f"esperado objeto em 'data'. Chaves disponiveis no topo: {chaves}"
        )

    rows = data.get("list")
    if not isinstance(rows, list):
        chaves_data = sorted(data.keys())
        print(f"Chaves disponiveis em resposta['data']: {chaves_data}")
        raise ValueError(
            "Estrutura inesperada na resposta de /general: "
            "esperado lista em resposta['data']['list']."
        )

    return pd.DataFrame(rows)


def padronizar_dataframe_dados_gerais(
    df: pd.DataFrame,
    fluxo: str,
) -> pd.DataFrame:
    df_padronizado = df.copy()
    df_padronizado["fluxo"] = _normalizar_fluxo(fluxo)
    df_padronizado = df_padronizado.rename(columns=COLUMN_RENAMES)

    for column in ("ano", "mes_num"):
        if column in df_padronizado.columns:
            df_padronizado[column] = pd.to_numeric(
                df_padronizado[column],
                errors="coerce",
            ).astype("Int64")

    for column in ("valor_usd_fob", "kg_liquido", "quantidade_estatistica"):
        if column in df_padronizado.columns:
            df_padronizado[column] = pd.to_numeric(
                df_padronizado[column],
                errors="coerce",
            )

    for column in ("ncm_codigo", "isic_divisao_codigo"):
        if column in df_padronizado.columns:
            df_padronizado[column] = df_padronizado[column].map(_to_text_code)

    available_columns = [
        column for column in FINAL_COLUMN_ORDER if column in df_padronizado.columns
    ]
    return df_padronizado[available_columns]


def consultar_fluxo_uf_mes(
    fluxo: str,
    uf_codigo: str,
    data_inicio: str,
    data_fim: str,
) -> pd.DataFrame:
    payload = montar_payload_fluxo_uf_mes(
        fluxo=fluxo,
        uf_codigo=uf_codigo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    resposta = consultar_dados_gerais(payload)
    df = normalizar_resposta_dados_gerais(resposta)
    return padronizar_dataframe_dados_gerais(df, fluxo=fluxo)


def _normalizar_fluxo(fluxo: str) -> str:
    if fluxo == "export":
        return "exportacao"
    if fluxo == "import":
        return "importacao"
    return fluxo


def _to_text_code(value: Any) -> Any:
    if pd.isna(value):
        return pd.NA

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value).strip()
