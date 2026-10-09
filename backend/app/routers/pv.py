from decimal import Decimal
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.crud import equipment as equipment_crud, property as property_crud, pv as pv_crud
from app.database import get_db
from app.schemas.pv import PVProposalRead, PVSimulationRead, PVSimulationRequest
from app.schemas.pv_catalog import PVBattery, PVInverter, PVModule
from app.services.pv_catalog import PVCatalogStore
from app.services.pv_simulation import (
    PVSimulationDomainError,
    proposal_from_simulation,
    simulate_pv_solution,
)


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Fotovoltaico"])
catalog_store = PVCatalogStore()
catalog_load_error = None
try:
    catalog_store.reload()
except Exception as error:
    catalog_load_error = error
    logger.exception("Falha ao carregar atomicamente os catálogos fotovoltaicos")


ERROR_RESPONSES = {
    401: {"description": "Token ausente ou inválido"},
    404: {"description": "Residência ou proposta não encontrada para o usuário"},
    409: {"description": "Consumo ausente ou combinação técnica incompatível"},
    422: {"description": "Parâmetro de entrada inválido"},
}


def _owned_property_or_404(db: Session, property_id: int, user_id: int):
    owned = property_crud.get_property(db, property_id, user_id)
    if owned is None:
        raise HTTPException(status_code=404, detail="Residência não encontrada")
    return owned


def _catalog_or_500():
    if catalog_load_error is not None:
        raise HTTPException(
            status_code=500,
            detail="Catálogo fotovoltaico indisponível; consulte os logs da aplicação",
        )
    return catalog_store.catalog


def _simulate(db: Session, property_id: int, user_id: int, request: PVSimulationRequest):
    _owned_property_or_404(db, property_id, user_id)
    report = equipment_crud.get_consumption_report(db, property_id, user_id)
    consumption = Decimal(str(report.total_monthly_consumption_kwh))
    try:
        return simulate_pv_solution(
            property_id,
            consumption,
            request,
            _catalog_or_500(),
            report.created_at,
        )
    except PVSimulationDomainError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"field": error.field, "message": error.message},
        ) from error
    except ValueError as error:
        field = getattr(error, "field", "configuration")
        message = getattr(error, "message", str(error))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"field": field, "message": message},
        ) from error


@router.get(
    "/api/pv/datasets/modules",
    response_model=List[PVModule],
    responses={401: ERROR_RESPONSES[401]},
    summary="Lista módulos FV validados",
)
async def list_modules(current_user=Depends(get_current_active_user)):
    return _catalog_or_500().modules


@router.get(
    "/api/pv/datasets/inverters",
    response_model=List[PVInverter],
    responses={401: ERROR_RESPONSES[401]},
    summary="Lista inversores validados",
)
async def list_inverters(current_user=Depends(get_current_active_user)):
    return _catalog_or_500().inverters


@router.get(
    "/api/pv/datasets/batteries",
    response_model=List[PVBattery],
    responses={401: ERROR_RESPONSES[401]},
    summary="Lista baterias validadas",
)
async def list_batteries(current_user=Depends(get_current_active_user)):
    return _catalog_or_500().batteries


@router.post(
    "/api/properties/{property_id}/pv/simulations",
    response_model=PVSimulationRead,
    responses=ERROR_RESPONSES,
    summary="Simula uma solução FV sem persistir",
)
async def simulate(
    property_id: int,
    request: PVSimulationRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _simulate(db, property_id, current_user.id, request)


@router.post(
    "/api/properties/{property_id}/pv/proposals",
    response_model=PVProposalRead,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Revalida e salva uma proposta FV",
)
async def create_proposal(
    property_id: int,
    request: PVSimulationRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    result = _simulate(db, property_id, current_user.id, request)
    try:
        payload = proposal_from_simulation(request, result)
    except PVSimulationDomainError as error:
        raise HTTPException(
            status_code=409, detail={"field": error.field, "message": error.message}
        ) from error
    return pv_crud.create_proposal(db, property_id, current_user.id, payload)


@router.get(
    "/api/properties/{property_id}/pv/proposals",
    response_model=List[PVProposalRead],
    responses={401: ERROR_RESPONSES[401], 404: ERROR_RESPONSES[404], 422: ERROR_RESPONSES[422]},
    summary="Lista propostas FV da residência",
)
async def list_proposals(
    property_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _owned_property_or_404(db, property_id, current_user.id)
    return pv_crud.list_proposals(db, property_id, current_user.id, skip, limit)


@router.get(
    "/api/properties/{property_id}/pv/proposals/{proposal_id}",
    response_model=PVProposalRead,
    responses={401: ERROR_RESPONSES[401], 404: ERROR_RESPONSES[404], 422: ERROR_RESPONSES[422]},
    summary="Consulta uma proposta FV completa",
)
async def get_proposal(
    property_id: int,
    proposal_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    proposal = pv_crud.get_proposal(db, property_id, proposal_id, current_user.id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    return proposal


@router.put(
    "/api/properties/{property_id}/pv/proposals/{proposal_id}",
    response_model=PVProposalRead,
    responses=ERROR_RESPONSES,
    summary="Recalcula e substitui integralmente uma proposta FV",
)
async def update_proposal(
    property_id: int,
    proposal_id: int,
    request: PVSimulationRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if pv_crud.get_proposal(db, property_id, proposal_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    result = _simulate(db, property_id, current_user.id, request)
    try:
        payload = proposal_from_simulation(request, result)
    except PVSimulationDomainError as error:
        raise HTTPException(
            status_code=409, detail={"field": error.field, "message": error.message}
        ) from error
    return pv_crud.replace_proposal(
        db, property_id, proposal_id, current_user.id, payload
    )


@router.delete(
    "/api/properties/{property_id}/pv/proposals/{proposal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: ERROR_RESPONSES[401], 404: ERROR_RESPONSES[404]},
    summary="Exclui uma proposta FV",
)
async def delete_proposal(
    property_id: int,
    proposal_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not pv_crud.delete_proposal(db, property_id, proposal_id, current_user.id):
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
