from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models.product import Product
from ..utils.deps import require_role

router = APIRouter()

class ProductCreate(BaseModel):
    name: str
    spec: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = "manual"
    source_msg_id: Optional[int] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    spec: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None

@router.get("/")
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取产品列表（分页 + 搜索）"""
    query = db.query(Product)
    
    # 搜索过滤
    if keyword:
        query = query.filter(Product.name.contains(keyword))
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    products = query.offset(offset).limit(size).all()
    
    product_list = []
    for product in products:
        product_list.append({
            "id": product.id,
            "name": product.name,
            "spec": product.spec,
            "category": product.category,
            "unit_price": float(product.unit_price) if product.unit_price else None,
            "unit": product.unit,
            "source": product.source,
            "source_msg_id": product.source_msg_id,
            "status": product.status,
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        })
    
    return {
        "code": 0,
        "data": {
            "items": product_list,
            "total": total,
            "page": page,
            "size": size
        },
        "message": "ok"
    }

@router.post("/")
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin", "reviewer"))
):
    """创建产品"""
    new_product = Product(
        name=product_data.name,
        spec=product_data.spec,
        category=product_data.category,
        unit_price=product_data.unit_price,
        unit=product_data.unit,
        source=product_data.source,
        source_msg_id=product_data.source_msg_id
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return {
        "code": 0,
        "data": {
            "id": new_product.id,
            "name": new_product.name,
            "spec": new_product.spec,
            "category": new_product.category,
            "unit_price": float(new_product.unit_price) if new_product.unit_price else None,
            "unit": new_product.unit,
            "source": new_product.source,
            "source_msg_id": new_product.source_msg_id,
            "status": new_product.status
        },
        "message": "ok"
    }

@router.put("/{product_id}")
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin", "reviewer"))
):
    """更新产品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    # 更新字段
    if product_data.name is not None:
        product.name = product_data.name
    if product_data.spec is not None:
        product.spec = product_data.spec
    if product_data.category is not None:
        product.category = product_data.category
    if product_data.unit_price is not None:
        product.unit_price = product_data.unit_price
    if product_data.unit is not None:
        product.unit = product_data.unit
    if product_data.status is not None:
        product.status = product_data.status
    
    db.commit()
    db.refresh(product)
    
    return {
        "code": 0,
        "data": {
            "id": product.id,
            "name": product.name,
            "spec": product.spec,
            "category": product.category,
            "unit_price": float(product.unit_price) if product.unit_price else None,
            "unit": product.unit,
            "source": product.source,
            "source_msg_id": product.source_msg_id,
            "status": product.status
        },
        "message": "ok"
    }