from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from backend.app.repositories.feature_store_repository import DatasetInvalidError, DatasetNotFoundError
from backend.app.schemas.token_display import ApiEnvelope, MetaModel
from backend.app.services.token_page_service import TokenNotSupportedError, TokenPageService

router = APIRouter(prefix="/tokens", tags=["token-display"])
PROJECT_ROOT = Path(__file__).resolve().parents[5]
service = TokenPageService(PROJECT_ROOT)


def build_envelope(data: object, degraded: bool = False) -> ApiEnvelope[object]:
    return ApiEnvelope(
        code="OK",
        message="success",
        request_id=f"req_{uuid4().hex[:12]}",
        data=data,
        meta=MetaModel(token_symbol="FET", chain_name="ethereum", degraded=degraded),
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


@router.get("/fet/page")
def get_fet_page(
    chart_days: int = Query(default=30),
    top_limit: int = Query(default=10),
    profile_limit: int = Query(default=6),
) -> ApiEnvelope[object]:
    try:
        data = service.get_page("FET", chart_days=chart_days, top_limit=top_limit, profile_limit=profile_limit)
        return build_envelope(data)
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/fet/summary")
def get_fet_summary() -> ApiEnvelope[object]:
    try:
        return build_envelope(service.get_summary("FET"))
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/fet/charts")
def get_fet_charts(days: int = Query(default=30)) -> ApiEnvelope[object]:
    try:
        return build_envelope(service.get_charts("FET", days=days))
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/fet/top-addresses")
def get_fet_top_addresses(
    limit: int = Query(default=10),
    sort_by: str = Query(default="position_value_usd"),
    order: str = Query(default="desc"),
) -> ApiEnvelope[object]:
    try:
        return build_envelope(service.get_top_addresses("FET", limit=limit, sort_by=sort_by, order=order))
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/fet/address-profiles")
def get_fet_address_profiles(limit: int = Query(default=6)) -> ApiEnvelope[object]:
    try:
        return build_envelope(service.get_address_profiles("FET", limit=limit))
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc


@router.get("/fet/dune-embeds")
def get_fet_dune_embeds() -> ApiEnvelope[object]:
    try:
        return build_envelope(service.get_dune_embeds("FET"), degraded=True)
    except Exception as exc:  # noqa: BLE001
        raise map_error(exc) from exc
