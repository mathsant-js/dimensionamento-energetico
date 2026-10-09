from typing import Optional

from sqlalchemy.orm import Session, joinedload

from ..models import PVProposal, PVProposalItem, Property
from ..schemas.pv import PVProposalCreate


def _owned_property(db: Session, property_id: int, user_id: int) -> Optional[Property]:
    return db.query(Property).filter(Property.id == property_id, Property.user_id == user_id).first()


def create_proposal(
    db: Session, property_id: int, user_id: int, proposal: PVProposalCreate
) -> Optional[PVProposal]:
    """Create a proposal only under a property owned by ``user_id``."""
    if _owned_property(db, property_id, user_id) is None:
        return None

    data = proposal.model_dump(exclude={"items"})
    db_proposal = PVProposal(property_id=property_id, user_id=user_id, **data)
    db_proposal.items = [PVProposalItem(**item.model_dump()) for item in proposal.items]
    db.add(db_proposal)
    db.commit()
    return get_proposal(db, property_id, db_proposal.id, user_id)


def get_proposal(
    db: Session, property_id: int, proposal_id: int, user_id: int
) -> Optional[PVProposal]:
    return (
        db.query(PVProposal)
        .join(Property, PVProposal.property_id == Property.id)
        .options(joinedload(PVProposal.items))
        .filter(
            PVProposal.id == proposal_id,
            PVProposal.property_id == property_id,
            PVProposal.user_id == user_id,
            Property.user_id == user_id,
        )
        .first()
    )


def list_proposals(
    db: Session, property_id: int, user_id: int, skip: int = 0, limit: int = 100
):
    if _owned_property(db, property_id, user_id) is None:
        return []
    return (
        db.query(PVProposal)
        .join(Property, PVProposal.property_id == Property.id)
        .options(joinedload(PVProposal.items))
        .filter(
            PVProposal.property_id == property_id,
            PVProposal.user_id == user_id,
            Property.user_id == user_id,
        )
        .order_by(PVProposal.created_at.desc(), PVProposal.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def replace_proposal(
    db: Session,
    property_id: int,
    proposal_id: int,
    user_id: int,
    proposal: PVProposalCreate,
) -> Optional[PVProposal]:
    """Atomically replace the calculation and its item snapshots."""
    db_proposal = get_proposal(db, property_id, proposal_id, user_id)
    if db_proposal is None:
        return None

    for field, value in proposal.model_dump(exclude={"items"}).items():
        setattr(db_proposal, field, value)
    db_proposal.items.clear()
    db.flush()
    db_proposal.items.extend(PVProposalItem(**item.model_dump()) for item in proposal.items)
    db.commit()
    return get_proposal(db, property_id, proposal_id, user_id)


def delete_proposal(db: Session, property_id: int, proposal_id: int, user_id: int) -> bool:
    db_proposal = get_proposal(db, property_id, proposal_id, user_id)
    if db_proposal is None:
        return False
    db.delete(db_proposal)
    db.commit()
    return True
