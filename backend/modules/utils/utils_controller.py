from fastapi import APIRouter, Depends
from pydantic import EmailStr

from api.deps import get_current_active_superuser
from modules.auth.auth_model import Message
from modules.utils.utils_service import generate_test_email, send_email


router = APIRouter(prefix="/utils", tags=["Utils"])

@router.post(
    "/test-email",
    operation_id="test_email",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr):
    """
    Test emails
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get(
    "/health-check",
    operation_id="health_check",
)
async def health_check() -> bool:
    return True
