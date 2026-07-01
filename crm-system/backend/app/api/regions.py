from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.region import Region
from ..utils.deps import require_role

router = APIRouter()

class RegionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class RegionUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None

@router.get("/")
async def list_regions(db: Session = Depends(get_db)):
    """获取区域列表"""
    regions = db.query(Region).filter(Region.status == 1).all()
    
    region_list = []
    for region in regions:
        region_list.append({
            "id": region.id,
            "name": region.name,
            "code": region.code,
            "description": region.description,
            "status": region.status,
            "created_at": region.created_at.isoformat() if region.created_at else None,
            "updated_at": region.updated_at.isoformat() if region.updated_at else None
        })
    
    return {
        "code": 0,
        "data": region_list,
        "message": "ok"
    }

@router.post("/")
async def create_region(
    region_data: RegionCreate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """创建区域"""
    # 检查区域名称是否已存在
    existing_region = db.query(Region).filter(Region.name == region_data.name).first()
    if existing_region:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="区域名称已存在"
        )
    
    # 检查区域代码是否已存在
    existing_code = db.query(Region).filter(Region.code == region_data.code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="区域代码已存在"
        )
    
    # 创建新区域
    new_region = Region(
        name=region_data.name,
        code=region_data.code,
        description=region_data.description
    )
    
    db.add(new_region)
    db.commit()
    db.refresh(new_region)
    
    return {
        "code": 0,
        "data": {
            "id": new_region.id,
            "name": new_region.name,
            "code": new_region.code,
            "description": new_region.description,
            "status": new_region.status
        },
        "message": "ok"
    }

@router.put("/{region_id}")
async def update_region(
    region_id: int,
    region_data: RegionUpdate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """更新区域"""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    
    # 更新字段
    if region_data.name is not None:
        # 检查名称是否与其他区域重复
        existing = db.query(Region).filter(Region.name == region_data.name, Region.id != region_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="区域名称已存在"
            )
        region.name = region_data.name
    
    if region_data.code is not None:
        # 检查代码是否与其他区域重复
        existing = db.query(Region).filter(Region.code == region_data.code, Region.id != region_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="区域代码已存在"
            )
        region.code = region_data.code
    
    if region_data.description is not None:
        region.description = region_data.description
    if region_data.status is not None:
        region.status = region_data.status
    
    db.commit()
    db.refresh(region)
    
    return {
        "code": 0,
        "data": {
            "id": region.id,
            "name": region.name,
            "code": region.code,
            "description": region.description,
            "status": region.status
        },
        "message": "ok"
    }

@router.delete("/{region_id}")
async def delete_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """删除区域（软删除）"""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    
    # 软删除：设置 status=0
    region.status = 0
    db.commit()
    
    return {
        "code": 0,
        "data": None,
        "message": "区域已禁用"
    }