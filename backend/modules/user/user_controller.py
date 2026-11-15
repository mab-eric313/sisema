from typing import Annotated, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete, func, select

from api.deps import CurrentUser, SessionDep, get_current_active_superuser
from core.config import Settings
from modules.user import user_repository as crud
from modules.auth.auth_model import (
    Message, 
)
from modules.auth.auth_service import (
    get_password_hash,
    verify_password, 
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

router = APIRouter(prefix="/user", tags=["User"])


@router.post(
    "/private-user/", 
    operation_id="create_private_user",
    response_model=UserPublic
)
def create_private_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new private user
    """
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()

    return user


@router.get(
    "/", 
    operation_id="read_users",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users
    """
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = (
        select(User)
        .order_by(col(User.created_at).desc())
        .offset(skip).limit(limit)
    )
    users = session.exec(statement).all()

    users_public = [UserPublic.model_validate(user) for user in users]
    return UsersPublic(data=users_public, count=count)


@router.post(
    "/", 
    operation_id="create_user",
    dependencies=[Depends(get_current_active_superuser)], 
    response_model=UserPublic
)
def create_user(*, user_in: UserCreate, session: SessionDep) -> Any:
    """
    Create new user
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if Settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, 
            username=user_in.email, 
            password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    return user


@router.post(
    "/me", 
    operation_id="update_user_me",
    response_model=UserPublic
)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
):
    """
    Update own user
    """
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=400, detail="User with this email already exists"
            )

    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)


@router.patch(
    "/me/password", 
    operation_id="update_password_me",
    response_model=Message
)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password
    """
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )

    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password

    session.add(current_user)
    session.commit()

    return Message(message="Password updated succesfully")


@router.get(
    "/me", 
    operation_id="read_user_me",
    response_model=UserPublic
)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user
    """
    return current_user


@router.delete(
    "/me", 
    operation_id="delete_user_me",
    response_model=Message
)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )

    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.get(
    "/{user_id}", 
    operation_id="read_user_by_id",
    response_model=UserPublic
)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch(
    "/{user_id}",
    operation_id="update_user",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic
)
def update_user(
    *, 
    session: SessionDep, 
    user_id: uuid.UUID, 
    user_in: UserUpdate
) -> Any:
    """
    Update a user
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(
            session=session, 
            email=user_in.email
        )
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists"
            )

    user = crud.update_user(session=session, db_user=user, user_in=user_in)

    return user


@router.delete(
    "/{user_id}", 
    operation_id="delete_user",
    dependencies=[Depends(get_current_active_superuser)]
)
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403,
            detail="Super users are not allowed to delete themselves"
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)

    session.exec(statement)
    session.delete(user)
    session.commit()

    return Message(message="User deleted successfully")

