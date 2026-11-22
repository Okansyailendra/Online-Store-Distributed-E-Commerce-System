import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from backend.common.db_client import db_client
from backend.server3_api.schemas import RegisterRequest, LoginRequest
from backend.server3_api.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    existing = db_client.query_one("SELECT id FROM users WHERE email = :email", {"email": req.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alamat email sudah terdaftar.")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(req.password)
    sql = """
    INSERT INTO users (id, email, password_hash, full_name, phone_number, role)
    VALUES (:id, :email, :password_hash, :full_name, :phone_number, 'CUSTOMER')
    """
    db_client.execute(sql, {
        "id": user_id,
        "email": req.email,
        "password_hash": pw_hash,
        "full_name": req.full_name,
        "phone_number": req.phone_number
    })

    return {
        "success": True,
        "message": "Registrasi akun berhasil.",
        "data": {
            "user_id": user_id,
            "email": req.email,
            "full_name": req.full_name,
            "role": "CUSTOMER"
        }
    }

@router.post("/login")
def login(req: LoginRequest):
    user = db_client.query_one("SELECT id, email, password_hash, full_name, role FROM users WHERE email = :email", {"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kombinasi email atau kata sandi tidak valid.")

    token = create_access_token(user_id=user["id"], email=user["email"], role=user["role"])
    return {
        "success": True,
        "message": "Login berhasil.",
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            }
        }
    }

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return {"success": True, "data": user}
