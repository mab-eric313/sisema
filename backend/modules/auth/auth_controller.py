from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import col, delete, func, select

from modules.auth import auth_repository as auth_crud
from modules.user import user_repository as user_crud
from api.deps import CurrentUser, SessionDep, get_current_active_superuser
from modules.auth.auth_service import (
    create_access_token,
    generate_password_reset_token,
    get_password_hash,
    verify_password, 
    verify_password_reset_token
)
from core.config import settings
from modules.auth.auth_model import (
    Message, 
    NewPassword,
    Token,
)
from modules.user.user_model import (
    PrivateUserCreate, 
    UpdatePassword,
    User,
    UserCreate, 
    UserPublic,
    UserRegister, 
    UserUpdate,
    UserUpdateMe,
    UsersPublic,
)
from modules.item.item_model import Item
from modules.utils.utils_service import (
    generate_new_account_email, 
    generate_reset_password_email, 
    send_email
)

router = APIRouter(prefix="/auth", tags=["Authenticate"])


@router.post(
    "/login/access-token",
    operation_id="login_access_token",
)
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = auth_crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post(
    "/signup", 
    operation_id="register_user",
    response_model=UserPublic
)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to logged in
    """
    user = user_crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    user_create = UserCreate.model_validate(user_in)
    user = user_crud.create_user(session=session, user_create=user_create)

    return user


@router.post(
    "/login/test-token", 
    operation_id="test_token",
    response_model=UserPublic
)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post(
    "/password-recovery/{email}",
    operation_id="recover_password",
)
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = user_crud.get_user_by_email(session=session, email=email)

    # Always return the same response to prevent email enumeration attacks
    # Only send email if user actually exists
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post(
    "/reset-password/",
    operation_id="reset_password",
)
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = user_crud.get_user_by_email(session=session, email=email)
    if not user:
        # Don't reveal that the user doesn't exist - use same error as invalid token
        raise HTTPException(status_code=400, detail="Invalid token")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user_in_update = UserUpdate(password=body.new_password)
    user_crud.update_user(
        session=session,
        db_user=user,
        user_in=user_in_update,
    )
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    operation_id="recover_password_html_content",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = user_crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject": email_data.subject}
    )



