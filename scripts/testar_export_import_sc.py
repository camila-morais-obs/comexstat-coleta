from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from comexstat.dados_gerais import (  # noqa: E402
    consultar_dados_gerais,
    montar_payload_fluxo_uf_mes,
    normalizar_resposta_dados_gerais,
    padronizar_dataframe_dados_gerais,
)


UF_SC = "44"
DATA_INICIO = "2024-01"
DATA_FIM = "2024-01"

RAW_EXPORT_PATH = PROJECT_ROOT / "data" / "raw" / "teste_export_2024_01_sc.json"
RAW_IMPORT_PATH = PROJECT_ROOT / "data" / "raw" / "teste_import_2024_01_sc.json"
EXCEL_OUTPUT_PATH = (
    PROJECT_ROOT / "outputs" / "teste_export_import_2024_01_sc.xlsx"
)


def main() -> None:
    df_export = consultar_e_salvar_fluxo(
        fluxo="export",
        output_path=RAW_EXPORT_PATH,
    )
    print("\nAguardando 12 segundos antes da proxima consulta...")
    time.sleep(12)
    df_import = consultar_e_salvar_fluxo(
        fluxo="import",
        output_path=RAW_IMPORT_PATH,
    )

    df_final = pd.concat([df_export, df_import], ignore_index=True)
    EXCEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(EXCEL_OUTPUT_PATH, index=False)

    linhas_por_fluxo = df_final.groupby("fluxo").size()
    soma_por_fluxo = df_final.groupby("fluxo")["valor_usd_fob"].sum(min_count=1)

    print(f"Excel salvo em: {EXCEL_OUTPUT_PATH}")
    print("\nNumero de linhas por fluxo:")
    print(linhas_por_fluxo.to_string())
    print("\nColunas finais:")
    print(list(df_final.columns))
    print("\nSoma de valor_usd_fob por fluxo:")
    print(soma_por_fluxo.to_string())
    print("\nPrimeiras 10 linhas:")
    print(df_final.head(10).to_string(index=False))


def consultar_e_salvar_fluxo(fluxo: str, output_path: Path) -> pd.DataFrame:
    payload = montar_payload_fluxo_uf_mes(
        fluxo=fluxo,
        uf_codigo=UF_SC,
        data_inicio=DATA_INICIO,
        data_fim=DATA_FIM,
    )
    print(f"\nPayload {fluxo}:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    resposta = consultar_dados_gerais(payload)
    salvar_json_bruto(resposta, output_path)
    df = normalizar_resposta_dados_gerais(resposta)
    return padronizar_dataframe_dados_gerais(df, fluxo=fluxo)


def salvar_json_bruto(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"JSON bruto salvo em: {output_path}")


if __name__ == "__main__":
    main()
