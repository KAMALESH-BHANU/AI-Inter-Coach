import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, UserProfileResponse
from app.db.models import UserModel
from app.db.database import db
from app.utils.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# In-memory storage fallback if MongoDB is not reachable
MEMORY_USERS = {}

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if db.is_connected and db.db is not None:
        user_data = await db.db.users.find_one({"id": user_id})
        if user_data:
            return UserModel(**user_data)
    else:
        user = MEMORY_USERS.get(user_id)
        if user:
            return user
            
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    email_clean = req.email.strip().lower()
    
    # Check if user already exists
    if db.is_connected and db.db is not None:
        existing = await db.db.users.find_one({"email": email_clean})
        if existing:
            raise HTTPException(status_code=400, detail="An account with this email already exists")
    else:
        for u in MEMORY_USERS.values():
            if u.email == email_clean:
                raise HTTPException(status_code=400, detail="An account with this email already exists")

    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(req.password)
    new_user = UserModel(
        id=user_id,
        email=email_clean,
        full_name=req.full_name,
        hashed_password=hashed_pwd,
        skills=req.skills
    )

    if db.is_connected and db.db is not None:
        await db.db.users.insert_one(new_user.model_dump(mode="json"))
    else:
        MEMORY_USERS[user_id] = new_user

    token = create_access_token(data={"sub": user_id, "email": email_clean})
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        full_name=req.full_name,
        email=email_clean
    )

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    email_clean = req.email.strip().lower()
    user_data = None
    
    if db.is_connected and db.db is not None:
        user_data = await db.db.users.find_one({"email": email_clean})
        if user_data:
            user = UserModel(**user_data)
        else:
            user = None
    else:
        user = next((u for u in MEMORY_USERS.values() if u.email == email_clean), None)

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email
    )

@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        skills=current_user.skills,
        created_at=current_user.created_at
    )
