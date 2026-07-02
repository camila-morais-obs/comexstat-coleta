from __future__ import annotations

from typing import Any

import requests


BASE_URL = "https://api-comexstat.mdic.gov.br"
DEFAULT_TIMEOUT = 120
DEFAULT_PARAMS = {"language": "pt"}


class ComexStatApiError(RuntimeError):
    """Erro de comunicacao ou resposta invalida da API ComexStat."""


def get_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return _request_json("GET", path, params=params)


def post_json(
    path: str,
    payload: dict[str, Any],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _request_json("POST", path, params=params, json=payload)


def get_filter_values(base: str, filter_name: str) -> dict[str, Any]:
    base_path = base.strip("/")
    filter_path = filter_name.strip("/")
    return get_json(f"/{base_path}/filters/{filter_path}")


def _request_json(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = _build_url(path)
    request_params = {**DEFAULT_PARAMS, **(params or {})}

    try:
        response = requests.request(
            method=method,
            url=url,
            params=request_params,
            json=json,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ComexStatApiError(
            f"Falha ao acessar a API ComexStat em {url}: {exc}"
        ) from exc

    if not response.ok:
        raise ComexStatApiError(_format_http_error(response))

    try:
        return response.json()
    except ValueError as exc:
        raise ComexStatApiError(
            f"A API ComexStat respondeu com conteudo que nao e JSON em {url}."
        ) from exc


def _build_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BASE_URL}/{path.lstrip('/')}"


def _format_http_error(response: requests.Response) -> str:
    url = response.url or "<url desconhecida>"
    details = _extract_error_details(response)
    return (
        f"Erro HTTP {response.status_code} ao acessar {url}."
        f" Detalhes retornados pela API: {details}"
    )


def _extract_error_details(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return text or "<sem detalhes no corpo da resposta>"

    return repr(data)
