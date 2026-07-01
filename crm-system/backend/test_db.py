import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, SessionLocal
from app.models import *

def test_database():
    """测试数据库连接和种子数据"""
    print("测试数据库连接...")
    
    try:
        # 测试连接
        with engine.connect() as connection:
            print("数据库连接成功！")
        
        # 创建会话
        db = SessionLocal()
        
        # 查询区域数据
        regions = db.query(Region).all()
        print(f"区域数量: {len(regions)}")
        for region in regions:
            print(f"  - {region.name} ({region.code})")
        
        # 查询用户数据
        users = db.query(User).all()
        print(f"用户数量: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.role})")
        
        db.close()
        print("数据库测试完成！")
        
    except Exception as e:
        print(f"数据库测试失败: {e}")
        raise

if __name__ == "__main__":
    test_database()