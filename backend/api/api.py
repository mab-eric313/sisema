from fastapi import APIRouter

from api.routes import test
from modules.auth import auth_controller
from modules.item import item_controller
from modules.user import user_controller
from modules.utils import utils_controller


api_router = APIRouter()
api_router.include_router(test.router)
api_router.include_router(auth_controller.router)
api_router.include_router(item_controller.router)
api_router.include_router(user_controller.router)
api_router.include_router(utils_controller.router)
