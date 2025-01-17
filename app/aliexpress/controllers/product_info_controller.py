from flask import Blueprint, request
from app.aliexpress.services.product_info_service import ProductService
from app.common.utils.response_helper import ResponseHelper

# 创建蓝图
product_bp = Blueprint('aliexpress/product/info', __name__, url_prefix='/api/aliexpress/product/info')

class ProductController:
    """产品控制器"""
    
    _service = ProductService()
    
    @staticmethod
    @product_bp.route('/', methods=['GET'])
    def get_product_info():
        try:
            success, result = ProductController._service.get_product_info(1)
            if not success:
                return ResponseHelper.error(msg=result)
            return ResponseHelper.success(msg='获取产品信息成功', data=result)
        except Exception as e:
            return ResponseHelper.error(msg=f'获取产品信息失败: {str(e)}')

    @staticmethod
    @product_bp.route('/list', methods=['GET'])
    def list_products():
        try:
            success, result = ProductController._service.list_products()
            if not success:
                return ResponseHelper.error(msg=result)
            return ResponseHelper.success(msg='获取产品列表成功', data=result)
        except Exception as e:
            return ResponseHelper.error(msg=f'获取产品列表失败: {str(e)}')
