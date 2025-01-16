from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.core.services.database_manager import DatabaseManager

# 确保从 app.global_config 导入 global_config 字典
from global_config.base_config import config

db = SQLAlchemy()
# 创建全局数据库管理器实例
db_manager = DatabaseManager()

def create_app(config_name='default'):
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化 SQLAlchemy
    db.init_app(app)
    
    # 初始化数据库连接池
    with app.app_context():
        # 预热连接池，创建初始连接
        db_manager.warm_up()

    # 注册蓝图
    from app.aliexpress import product_bp, mabang_order_bp
    app.register_blueprint(product_bp)
    app.register_blueprint(mabang_order_bp)

    from app.core.controllers.file_controller import file_bp
    app.register_blueprint(file_bp, url_prefix='/api/file')

    with app.app_context():
        db.create_all()

    return app
