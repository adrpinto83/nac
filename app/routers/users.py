"""Users management router."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import get_db
from app.security import hash_password, decode_token

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    email: str = ""
    role: str = "user"


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool


async def verify_token(authorization: str = None) -> dict:
    """Verify token and return user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


@router.get("/", response_model=list[UserResponse])
async def list_users(authorization: str = None):
    """List all users."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, full_name, email, role, is_active FROM users"
    )
    users = await cursor.fetchall()
    await db.close()

    return [
        UserResponse(
            id=u[0],
            username=u[1],
            full_name=u[2],
            email=u[3],
            role=u[4],
            is_active=bool(u[5])
        )
        for u in users
    ]


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, authorization: str = None):
    """Create new user."""
    await verify_token(authorization)

    password_hash = hash_password(user.password)
    db = await get_db()

    try:
        cursor = await db.execute(
            "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
            (user.username, password_hash, user.full_name, user.email, user.role)
        )
        await db.commit()
        user_id = cursor.lastrowid

        return UserResponse(
            id=user_id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=True
        )
    except Exception as e:
        await db.close()
        raise HTTPException(status_code=400, detail=f"User creation failed: {str(e)}")
    finally:
        await db.close()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, authorization: str = None):
    """Get user by ID."""
    await verify_token(authorization)

    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, full_name, email, role, is_active FROM users WHERE id = ?",
        (user_id,)
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user[0],
        username=user[1],
        full_name=user[2],
        email=user[3],
        role=user[4],
        is_active=bool(user[5])
    )


@router.delete("/{user_id}")
async def delete_user(user_id: int, authorization: str = None):
    """Delete user."""
    await verify_token(authorization)

    db = await get_db()
    await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    await db.commit()
    await db.close()

    return {"message": "User deleted"}
