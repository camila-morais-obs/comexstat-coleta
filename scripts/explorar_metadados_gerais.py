from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from comexstat.client import get_json  # noqa: E402


DOCS_DIR = PROJECT_ROOT / "docs"
METADATA_TARGETS = {
    "general_details.json": "/general/details",
    "general_metrics.json": "/general/metrics",
    "general_filters.json": "/general/filters",
}


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for filename, endpoint in METADATA_TARGETS.items():
        data = get_json(endpoint)
        output_path = DOCS_DIR / filename
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n{endpoint}")
        print(f"Arquivo salvo em: {output_path}")
        _print_summary(data)


def _print_summary(data: Any) -> None:
    items = _normalize_items(data)
    print(f"Itens encontrados: {len(items)}")

    for index, item in enumerate(items[:20], start=1):
        label = _best_label(item)
        print(f"{index}. {label}")

    if len(items) > 20:
        print("... resumo limitado aos 20 primeiros itens.")


def _normalize_items(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("data", "result", "results", "items", "content"):
            value = data.get(key)
            if isinstance(value, list):
                return value

        return [data]

    return [data]


def _best_label(item: Any) -> str:
    if not isinstance(item, dict):
        return repr(item)

    for key in (
        "name",
        "nome",
        "label",
        "descricao",
        "description",
        "id",
        "code",
        "codigo",
    ):
        value = item.get(key)
        if value not in (None, ""):
            return f"{key}={value!r}"

    return repr(item)


if __name__ == "__main__":
    main()
