from __future__ import annotations

from typing import Any

import pandas as pd

from comexstat.client import post_json


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
