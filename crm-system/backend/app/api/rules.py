from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..database import get_db
from ..models.extract_rules import ExtractRule
from ..models.assign_rules import AssignRule
from ..utils.deps import require_role

router = APIRouter()

# 提取规则相关
class ExtractRuleCreate(BaseModel):
    name: str
    rule_type: str  # keyword, regex, sender, group
    rule_config: Dict[str, Any]
    priority: Optional[int] = 0

class ExtractRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    status: Optional[int] = None

# 分配规则相关
class AssignRuleCreate(BaseModel):
    name: str
    rule_type: str  # region, load_balance, product, custom
    rule_config: Dict[str, Any]
    priority: Optional[int] = 0

class AssignRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    status: Optional[int] = None

# 提取规则 API
@router.get("/extract")
async def list_extract_rules(
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """获取提取规则列表"""
    rules = db.query(ExtractRule).order_by(ExtractRule.priority.desc()).all()
    
    rule_list = []
    for rule in rules:
        rule_list.append({
            "id": rule.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "rule_config": rule.rule_config,
            "priority": rule.priority,
            "status": rule.status,
            "created_at": rule.created_at.isoformat() if rule.created_at else None
        })
    
    return {
        "code": 0,
        "data": rule_list,
        "message": "ok"
    }

@router.post("/extract")
async def create_extract_rule(
    rule_data: ExtractRuleCreate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """创建提取规则"""
    new_rule = ExtractRule(
        name=rule_data.name,
        rule_type=rule_data.rule_type,
        rule_config=rule_data.rule_config,
        priority=rule_data.priority
    )
    
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    return {
        "code": 0,
        "data": {
            "id": new_rule.id,
            "name": new_rule.name,
            "rule_type": new_rule.rule_type,
            "rule_config": new_rule.rule_config,
            "priority": new_rule.priority,
            "status": new_rule.status
        },
        "message": "ok"
    }

@router.put("/extract/{rule_id}")
async def update_extract_rule(
    rule_id: int,
    rule_data: ExtractRuleUpdate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """更新提取规则"""
    rule = db.query(ExtractRule).filter(ExtractRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    # 更新字段
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.rule_type is not None:
        rule.rule_type = rule_data.rule_type
    if rule_data.rule_config is not None:
        rule.rule_config = rule_data.rule_config
    if rule_data.priority is not None:
        rule.priority = rule_data.priority
    if rule_data.status is not None:
        rule.status = rule_data.status
    
    db.commit()
    db.refresh(rule)
    
    return {
        "code": 0,
        "data": {
            "id": rule.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "rule_config": rule.rule_config,
            "priority": rule.priority,
            "status": rule.status
        },
        "message": "ok"
    }

# 分配规则 API
@router.get("/assign")
async def list_assign_rules(
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """获取分配规则列表"""
    rules = db.query(AssignRule).order_by(AssignRule.priority.desc()).all()
    
    rule_list = []
    for rule in rules:
        rule_list.append({
            "id": rule.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "rule_config": rule.rule_config,
            "priority": rule.priority,
            "status": rule.status,
            "created_at": rule.created_at.isoformat() if rule.created_at else None
        })
    
    return {
        "code": 0,
        "data": rule_list,
        "message": "ok"
    }

@router.post("/assign")
async def create_assign_rule(
    rule_data: AssignRuleCreate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """创建分配规则"""
    new_rule = AssignRule(
        name=rule_data.name,
        rule_type=rule_data.rule_type,
        rule_config=rule_data.rule_config,
        priority=rule_data.priority
    )
    
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    return {
        "code": 0,
        "data": {
            "id": new_rule.id,
            "name": new_rule.name,
            "rule_type": new_rule.rule_type,
            "rule_config": new_rule.rule_config,
            "priority": new_rule.priority,
            "status": new_rule.status
        },
        "message": "ok"
    }

@router.put("/assign/{rule_id}")
async def update_assign_rule(
    rule_id: int,
    rule_data: AssignRuleUpdate,
    db: Session = Depends(get_db),
    current_user: any = Depends(require_role("admin"))
):
    """更新分配规则"""
    rule = db.query(AssignRule).filter(AssignRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在"
        )
    
    # 更新字段
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.rule_type is not None:
        rule.rule_type = rule_data.rule_type
    if rule_data.rule_config is not None:
        rule.rule_config = rule_data.rule_config
    if rule_data.priority is not None:
        rule.priority = rule_data.priority
    if rule_data.status is not None:
        rule.status = rule_data.status
    
    db.commit()
    db.refresh(rule)
    
    return {
        "code": 0,
        "data": {
            "id": rule.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "rule_config": rule.rule_config,
            "priority": rule.priority,
            "status": rule.status
        },
        "message": "ok"
    }