from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1.endpoints.token_display import router as token_display_router

router = APIRouter(prefix="/api/v1")
router.include_router(token_display_router)
