from fastapi import APIRouter, Depends, Request

from ...core.security import current_user

router = APIRouter(
    prefix="/api", tags=["Sistema"], dependencies=[Depends(current_user)]
)


@router.get("/config")
async def configuration(request: Request):
    settings = request.app.state.settings

    return {
        "business_name": settings.business_name,
        "tax_rate": str(settings.tax_rate),
        "currency": "MXN",
        "prices_include_tax": True,
    }
