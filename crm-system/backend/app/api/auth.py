from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..services.auth_service import authenticate_user, create_user_token, get_user_info
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if user.status == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    token = create_user_token(user)
    user_info = get_user_info(user)
    
    return {
        "code": 0,
        "data": {
            "token": token,
            "user": user_info
        },
        "message": "ok"
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    user_info = get_user_info(current_user)
    return {
        "code": 0,
        "data": user_info,
        "message": "ok"
    }