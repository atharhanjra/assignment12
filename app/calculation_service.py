"""
Functions for saving calculations in the database.
"""

from sqlalchemy.orm import Session

from app.calculation_factory import CalculationFactory
from app.models.calculation import Calculation
from app.schemas.calculation import CalculationCreate


def create_calculation(db: Session, calc_in: CalculationCreate) -> Calculation:
    """
    Compute the result with the factory, then save the calculation.

    Raises sqlalchemy.exc.IntegrityError if user_id does not match a real user.
    """
    calc_type = calc_in.type.value
    result = CalculationFactory.compute(calc_type, calc_in.a, calc_in.b)
    calculation = Calculation(
        a=calc_in.a,
        b=calc_in.b,
        type=calc_type,
        result=result,
        user_id=calc_in.user_id,
    )
    db.add(calculation)
    db.commit()
    db.refresh(calculation)
    return calculation

def list_calculations(db: Session):
    """Return every calculation, oldest first."""
    return db.query(Calculation).order_by(Calculation.id).all()


def get_calculation(db: Session, calc_id: int):
    """Return one calculation, or None if it doesn't exist."""
    return db.get(Calculation, calc_id)


def update_calculation(db: Session, calculation: Calculation, calc_in) -> Calculation:
    """Change a calculation's numbers or type, and recompute its result."""
    calculation.a = calc_in.a
    calculation.b = calc_in.b
    calculation.type = calc_in.type.value
    calculation.result = CalculationFactory.compute(calculation.type, calc_in.a, calc_in.b)
    db.commit()
    db.refresh(calculation)
    return calculation


def delete_calculation(db: Session, calculation: Calculation) -> None:
    """Remove a calculation."""
    db.delete(calculation)
    db.commit()