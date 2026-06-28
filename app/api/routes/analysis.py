from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_analysis_provider,
    get_current_user,
    get_db,
    get_rate_limiter,
)
from app.models.user import User
from app.schemas.analysis import AnalysisReportRequest, AnalysisReportResponse
from app.schemas.assets import ErrorResponse
from app.services import analysis
from app.services.analysis import AnalysisProvider
from app.services.rate_limits import (
    AI_ANALYSIS,
    RateLimitService,
    authenticated_effective_caller,
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid analysis request."},
    401: {"model": ErrorResponse, "description": "Missing or invalid access token."},
    403: {"model": ErrorResponse, "description": "User role cannot run analysis."},
    429: {"model": ErrorResponse, "description": "Analysis rate limit exceeded."},
    502: {"model": ErrorResponse, "description": "Analysis provider failed safely."},
    503: {"model": ErrorResponse, "description": "Analysis provider unavailable."},
}


@router.post(
    "/report",
    response_model=AnalysisReportResponse,
    response_model_exclude_none=True,
    summary="Generate a grounded organization-owned asset analysis report",
    responses=ERROR_RESPONSES,
)
async def generate_analysis_report(
    payload: AnalysisReportRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    rate_limiter: Annotated[RateLimitService, Depends(get_rate_limiter)],
    provider: Annotated[AnalysisProvider, Depends(get_analysis_provider)],
) -> AnalysisReportResponse:
    """Generate a bounded grounded analysis report for the current tenant."""
    await rate_limiter.check(
        AI_ANALYSIS,
        authenticated_effective_caller(current_user.id, current_user.organization_id),
    )
    return await analysis.generate_report(session, current_user, payload, provider)
