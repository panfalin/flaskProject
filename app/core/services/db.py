from app.core.services.database_manager import DatabaseManager

# 创建全局数据库实例
db = DatabaseManager()

# 导出这个实例供其他模块使用
__all__ = ['db']
