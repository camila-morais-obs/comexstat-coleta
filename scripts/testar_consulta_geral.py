from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from comexstat.client import get_filter_values  # noqa: E402
from comexstat.dados_gerais import (  # noqa: E402
    consultar_dados_gerais,
    montar_payload_dados_gerais,
    normalizar_resposta_dados_gerais,
)


RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "teste_export_2024_01_sc.json"
EXCEL_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "teste_export_2024_01_sc.xlsx"


def main() -> None:
    filtros_estado = get_filter_values("general", "state")
    estado_id = localizar_santa_catarina(filtros_estado)

    payload = montar_payload_dados_gerais(
        fluxo="export",
        data_inicio="2024-01",
        data_fim="2024-01",
        detalhes=["state", "ISICDivision", "ncm", "country"],
        metricas=["metricFOB", "metricKG", "metricStatistic"],
        filtros=[criar_filtro_estado(estado_id)],
        detalhar_mes=True,
    )

    print("Payload enviado:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    resposta = consultar_dados_gerais(payload)
    salvar_json_bruto(resposta, RAW_OUTPUT_PATH)

    df = normalizar_resposta_dados_gerais(resposta)
    EXCEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(EXCEL_OUTPUT_PATH, index=False)

    print(f"\nJSON bruto salvo em: {RAW_OUTPUT_PATH}")
    print(f"Excel salvo em: {EXCEL_OUTPUT_PATH}")
    print(f"Quantidade de linhas retornadas: {len(df)}")
    print(f"Nomes das colunas retornadas: {list(df.columns)}")
    print("\nPrimeiras 10 linhas:")
    print(df.head(10).to_string(index=False))


def localizar_santa_catarina(filtros_estado: dict[str, Any]) -> str:
    candidatos = extrair_lista_api(filtros_estado)

    for item in candidatos:
        if isinstance(item, dict) and item.get("text") == "Santa Catarina":
            print(f"UF localizada: {item}")
            print(f"Valor usado no filtro state: {item['id']}")
            return item["id"]

    for item in candidatos:
        if isinstance(item, dict) and corresponde_a_santa_catarina(item):
            estado_id = item.get("id")
            if estado_id is not None:
                print(f"UF localizada: {item}")
                print(f"Valor usado no filtro state: {estado_id}")
                return estado_id

    raise ValueError(
        "Nao foi possivel localizar Santa Catarina entre os valores do filtro 'state'."
    )


def criar_filtro_estado(valor: str) -> dict[str, Any]:
    return {
        "filter": "state",
        "values": [valor],
    }


def salvar_json_bruto(data: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def extrair_lista_api(resposta: Any) -> list[Any]:
    if isinstance(resposta, list):
        return _desaninhar_lista(resposta)

    if isinstance(resposta, dict):
        data = resposta.get("data")
        if isinstance(data, dict):
            data_list = data.get("list")
            if isinstance(data_list, list):
                return _desaninhar_lista(data_list)

        list_top = resposta.get("list")
        if isinstance(list_top, list):
            return _desaninhar_lista(list_top)

        if isinstance(data, list):
            return _desaninhar_lista(data)

    raise ValueError(
        "Nao foi possivel extrair uma lista da resposta da API. "
        f"Tipo recebido: {type(resposta).__name__}"
    )


def _desaninhar_lista(items: list[Any]) -> list[Any]:
    if len(items) == 1 and isinstance(items[0], list):
        return items[0]
    return items


def corresponde_a_santa_catarina(item: dict[str, Any]) -> bool:
    text = item.get("text")
    if isinstance(text, str) and normalizar_texto(text) == "santa catarina":
        return True

    for value in item.values():
        if isinstance(value, str) and "santa catarina" in normalizar_texto(value):
            return True

    return False


def normalizar_texto(texto: str) -> str:
    texto_ascii = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")
    return texto_ascii.decode("ascii").strip().lower()


if __name__ == "__main__":
    main()
