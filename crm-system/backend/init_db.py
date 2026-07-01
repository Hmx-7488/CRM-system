import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import *
from app.utils.security import hash_password

def init_database():
    """初始化数据库：建表 + 插入种子数据"""
    print("开始初始化数据库...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 检查区域是否已有数据
        existing_regions = db.query(Region).count()
        if existing_regions == 0:
            # 插入区域种子数据
            regions = [
                Region(name="华东", code="east_china", description="华东地区"),
                Region(name="华南", code="south_china", description="华南地区"),
                Region(name="华北", code="north_china", description="华北地区"),
                Region(name="西南", code="southwest", description="西南地区")
            ]
            db.add_all(regions)
            db.commit()
            print("区域种子数据插入完成")
        else:
            print(f"区域数据已存在，共 {existing_regions} 条")

        # 检查用户是否已有数据
        existing_users = db.query(User).count()
        if existing_users == 0:
            # 获取华东区域ID
            east_china = db.query(Region).filter(Region.code == "east_china").first()

            # 插入用户种子数据
            users = [
                User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    display_name="系统管理员",
                    role="admin",
                    region_id=east_china.id
                ),
                User(
                    username="review",
                    password_hash=hash_password("review123"),
                    display_name="审核员",
                    role="reviewer",
                    region_id=east_china.id
                ),
                User(
                    username="agent1",
                    password_hash=hash_password("agent123"),
                    display_name="操作员1",
                    role="agent",
                    region_id=east_china.id
                )
            ]
            db.add_all(users)
            db.commit()
            print("用户种子数据插入完成")
        else:
            print(f"用户数据已存在，共 {existing_users} 条")

        print("数据库初始化完成！")

    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()