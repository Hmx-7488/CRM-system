from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.user import User
from ..models.region import Region
from ..utils.deps import require_role
from ..utils.security import hash_password

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    role: str
    region_id: Optional[int] = None

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    region_id: Optional[int] = None
    status: Optional[int] = None

@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """获取用户列表（分页）"""
    offset = (page - 1) * size
    users = db.query(User).offset(offset).limit(size).all()
    total = db.query(User).count()
    
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "region_id": user.region_id,
            "region_name": user.region.name if user.region else None,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        })
    
    return {
        "code": 0,
        "data": {
            "items": user_list,
            "total": total,
            "page": page,
            "size": size
        },
        "message": "ok"
    }

@router.post("/")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """创建用户"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name,
        role=user_data.role,
        region_id=user_data.region_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "code": 0,
        "data": {
            "id": new_user.id,
            "username": new_user.username,
            "display_name": new_user.display_name,
            "role": new_user.role,
            "region_id": new_user.region_id,
            "status": new_user.status
        },
        "message": "ok"
    }

@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新字段
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.region_id is not None:
        user.region_id = user_data.region_id
    if user_data.status is not None:
        user.status = user_data.status
    
    db.commit()
    db.refresh(user)
    
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "region_id": user.region_id,
            "status": user.status
        },
        "message": "ok"
    }

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """禁用用户（软删除）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 软删除：设置 status=0
    user.status = 0
    db.commit()
    
    return {
        "code": 0,
        "data": None,
        "message": "用户已禁用"
    }