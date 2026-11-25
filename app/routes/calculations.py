"""
Calculation routes (BREAD): Browse, Read, Edit, Add, Delete.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.calculation_service import (
    create_calculation,
    delete_calculation,
    get_calculation,
    list_calculations,
    update_calculation,
)
from app.database import get_db
from app.models.user import User
from app.schemas.calculation import CalculationCreate, CalculationRead, CalculationUpdate

router = APIRouter(prefix="/calculations", tags=["calculations"])


def find_calculation(db: Session, calc_id: int):
    """Return the calculation, or stop with a 404 error if it doesn't exist."""
    calculation = get_calculation(db, calc_id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calculation


@router.get("", response_model=List[CalculationRead])
def browse_calculations(db: Session = Depends(get_db)):
    """Browse: return every calculation."""
    return list_calculations(db)


@router.get("/{calc_id}", response_model=CalculationRead)
def read_calculation(calc_id: int, db: Session = Depends(get_db)):
    """Read: return one calculation by its id."""
    return find_calculation(db, calc_id)


@router.put("/{calc_id}", response_model=CalculationRead)
def edit_calculation(calc_id: int, calc_in: CalculationUpdate, db: Session = Depends(get_db)):
    """Edit: change a calculation's numbers or type, and recompute the result."""
    calculation = find_calculation(db, calc_id)
    return update_calculation(db, calculation, calc_in)


@router.post("", response_model=CalculationRead, status_code=201)
def add_calculation(calc_in: CalculationCreate, db: Session = Depends(get_db)):
    """Add: create a new calculation for an existing user."""
    if db.get(User, calc_in.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return create_calculation(db, calc_in)


@router.delete("/{calc_id}", status_code=204)
def remove_calculation(calc_id: int, db: Session = Depends(get_db)):
    """Delete: remove a calculation by its id."""
    calculation = find_calculation(db, calc_id)
    delete_calculation(db, calculation)