"""
Pydantic schemas for calculation data.

CalculationCreate checks incoming data before it reaches the database.
CalculationRead is what the app sends back.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator


class CalculationType(str, Enum):
    """The only calculation types that are allowed."""

    ADD = "Add"
    SUB = "Sub"
    MULTIPLY = "Multiply"
    DIVIDE = "Divide"


class CalculationBase(BaseModel):
    """Fields shared by creating and editing a calculation."""

    a: float
    b: float
    type: CalculationType

    @model_validator(mode="after")
    def check_no_zero_divisor(self):
        """Reject division by zero before it reaches the database."""
        if self.type == CalculationType.DIVIDE and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationCreate(CalculationBase):
    """Data needed to create a calculation."""

    user_id: int


class CalculationUpdate(CalculationBase):
    """Data that can be changed when editing a calculation."""


class CalculationRead(BaseModel):
    """Calculation details returned by the app."""

    # Lets Pydantic read the values straight from a SQLAlchemy Calculation object
    model_config = ConfigDict(from_attributes=True)

    id: int
    a: float
    b: float
    type: CalculationType
    result: float
    user_id: int
    created_at: datetime