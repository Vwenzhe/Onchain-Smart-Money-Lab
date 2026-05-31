from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Query

from backend.app.repositories.feature_store_repository import DatasetInvalidError, DatasetNotFoundError
from backend.app.schemas.token_display import ApiEnvelope, MetaModel
from backend.app.services.token_page_service import TokenNotSupportedError, TokenPageService

router = APIRouter(prefix="/tokens", tags=["token-display"])
PROJECT_ROOT = Path(__file__).resolve().parents[5]
service = TokenPageService(PROJECT_ROOT)


def build_envelope(
    data: object,
    *,
    token_symbol: str,
    chain_name: str,
    degraded: bool = False,
) -> ApiEnvelope[object]:
    return ApiEnvelope(
        code="OK",
        message="success",
        request_id=f"req_{uuid4().hex[:12]}",
        data=data,
        meta=MetaModel(token_symbol=token_symbol.upper(), chain_name=chain_name, degraded=degraded),
    )


def map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TokenNotSupportedError):
        return HTTPException(status_code=400, detail={"code": "TOKEN_NOT_SUPPORTED", "message": str(exc)})
    if isinstance(exc, DatasetNotFoundError):
        return HTTPException(status_code=404, detail={"code": "DATASET_MISSING", "message": str(exc)})
    if isinstance(exc, DatasetInvalidError):
        return HTTPException(status_code=500, detail={"code": "DATASET_INVALID", "message": str(exc)})
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail={"code": "INVALID_QUERY_PARAM", "message": str(exc)})
    return HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(exc)})


def get_token_context(token_symbol: str) -> dict[str, str]:
    return service.get_token_meta(token_symbol)


@router.get("/{token_symbol}/page")
def get_token_page(
    token_symbol: str = FastAPIPath(..., description="Token symbol, e.g. fet / eth / pepe"),
    chart_days: int = Query(default=30),
    top_limit: int = Query(default=10),
    profile_limit: int = Query(default=6),
) -> ApiEnvelope[object]:
    try:
        context = get_token_context(token_symbol)
        data = service.get_page(
            context["token_symbol"],
            chart_days=chart_days,
            top_limit=top_limit,
            profile_limit=profile_limit,
        )
        return build_envelope(data, token_symbol=context["token_symbol"], chain_name=context["chain_name"])
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/{token_symbol}/summary")
def get_token_summary(
    token_symbol: str = FastAPIPath(..., description="Token symbol, e.g. fet / eth / pepe"),
) -> ApiEnvelope[object]:
    try:
        context = get_token_context(token_symbol)
        data = service.get_summary(context["token_symbol"])
        return build_envelope(data, token_symbol=context["token_symbol"], chain_name=context["chain_name"])
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/{token_symbol}/charts")
def get_token_charts(
    token_symbol: str = FastAPIPath(..., description="Token symbol, e.g. fet / eth / pepe"),
    days: int = Query(default=30),
) -> ApiEnvelope[object]:
    try:
        context = get_token_context(token_symbol)
        data = service.get_charts(context["token_symbol"], days=days)
        return build_envelope(data, token_symbol=context["token_symbol"], chain_name=context["chain_name"])
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/{token_symbol}/top-addresses")
def get_token_top_addresses(
    token_symbol: str = FastAPIPath(..., description="Token symbol, e.g. fet / eth / pepe"),
    limit: int = Query(default=10),
    sort_by: str = Query(default="position_value_usd"),
    order: str = Query(default="desc"),
) -> ApiEnvelope[object]:
    try:
        context = get_token_context(token_symbol)
        data = service.get_top_addresses(
            context["token_symbol"],
            limit=limit,
            sort_by=sort_by,
            order=order,
        )
        return build_envelope(data, token_symbol=context["token_symbol"], chain_name=context["chain_name"])
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/{token_symbol}/address-profiles")
def get_token_address_profiles(
    token_symbol: str = FastAPIPath(..., description="Token symbol, e.g. fet / eth / pepe"),
    limit: int = Query(default=6),
) -> ApiEnvelope[object]:
    try:
        context = get_token_context(token_symbol)
        data = service.get_address_profiles(context["token_symbol"], limit=limit)
        return build_envelope(data, token_symbol=context["token_symbol"], chain_name=context["chain_name"])
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/{token_symbol}/dune-embeds")
def get_token_dune_embeds(
    token_symbol: str = FastAPIPath(..., description="Token symbol, e.g. fet / eth / pepe"),
) -> ApiEnvelope[object]:
    try:
        context = get_token_context(token_symbol)
        data = service.get_dune_embeds(context["token_symbol"])
        return build_envelope(
            data,
            token_symbol=context["token_symbol"],
            chain_name=context["chain_name"],
            degraded=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc
