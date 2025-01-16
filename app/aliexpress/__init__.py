# AliExpress模块初始化文件

from flask import Blueprint

# 创建蓝图
product_bp = Blueprint('aliexpress/product/info', __name__, url_prefix='/api/aliexpress/product/info')

# 导入路由处理
from app.aliexpress.controllers import product_info_controller
