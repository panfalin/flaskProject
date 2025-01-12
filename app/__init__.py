from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 确保从 app.global_config 导入 global_config 字典
from global_config.base_config import config

db = SQLAlchemy()


def create_app(config_name='default'):
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])

    db.init_app(app)

    from app.aliexpress.controllers.user_controller import user_bp
    app.register_blueprint(user_bp)

    from app.aliexpress.controllers.product_info_controller import user_bp as aliexpress_bp
    app.register_blueprint(aliexpress_bp)

    from app.core.controllers.file_controller import file_bp
    app.register_blueprint(file_bp, url_prefix='/api/file')

    with app.app_context():
        db.create_all()

    return app
