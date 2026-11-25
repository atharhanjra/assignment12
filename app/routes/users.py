"""
User routes: register and login.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import LoginResponse, UserCreate, UserLogin, UserRead
from app.user_service import authenticate_user, create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new user. The password is hashed before it is saved."""
    try:
        return create_user(db, user_in)
    except IntegrityError:
        # The unique constraint on username or email was broken
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already registered")


@router.post("/login", response_model=LoginResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Check a username and password against the stored hash."""
    user = authenticate_user(db, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(message="Login successful", user=UserRead.model_validate(user))