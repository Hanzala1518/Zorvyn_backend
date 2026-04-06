import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.config import get_settings
from app.dependencies import get_current_user, get_supabase_admin_client
from app.services import auth_service, user_service, registration_service
from app.schemas.auth import TokenResponse, ChangePasswordRequest, RegisterRequest, RegisterResponse

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(body: RegisterRequest):
    """Public self-registration for viewer and analyst roles."""
    admin_client = get_supabase_admin_client()
    return registration_service.register_user(body, admin_client)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_client = get_supabase_admin_client()

    # Check approval / rejection status before full authentication.
    # Wrapped in try/except in case the approval_status column has not yet
    # been added via APPROVAL_FLOW_MIGRATION.sql — login still works without it.
    try:
        pre_check = (
            admin_client.table("users")
            .select("approval_status, status, is_deleted")
            .eq("email", form_data.username.lower().strip())
            .eq("is_deleted", False)
            .execute()
        )
        if pre_check.data:
            user_row = pre_check.data[0]
            if user_row.get("approval_status") == "pending_approval":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account is pending admin approval. You will be notified once approved.",
                )
            if user_row.get("approval_status") == "rejected":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your registration was not approved. Please contact an administrator.",
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Approval pre-check skipped (column may not exist yet): {exc}")

    user = auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
        client=admin_client,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"],
        },
        settings=settings,
    )
    logger.info(f"User logged in: {user['email']} role={user['role']}")
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    admin_client = get_supabase_admin_client()
    user_service.change_password(
        current_user["id"],
        body.current_password,
        body.new_password,
        admin_client,
    )
    return {"message": "Password changed successfully."}


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully."}
