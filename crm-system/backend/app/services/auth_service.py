from sqlalchemy.orm import Session
from ..models.user import User
from ..utils.security import verify_password, create_access_token

def authenticate_user(db: Session, username: str, password: str):
    """验证用户凭据"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user_token(user: User) -> str:
    """为用户创建访问令牌"""
    return create_access_token(data={"sub": str(user.id)})

def get_user_info(user: User) -> dict:
    """获取用户信息（不包含密码）"""
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "region_id": user.region_id,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }