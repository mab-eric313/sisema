from fastapi import APIRouter

router = APIRouter(tags=["test"])

@router.get("/hello-world")
def hello():
    return {"msg": "hello world"}
