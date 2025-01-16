import os
from flask import request, Blueprint
from werkzeug.utils import secure_filename
from app.aliexpress.services.mabang_order_service import MabangOrderService
from app.common.utils.response_helper import ResponseHelper
from app.aliexpress.app_config import UPLOAD_FOLDER

# 创建蓝图
mabang_order_bp = Blueprint('aliexpress/mabang/order', __name__, url_prefix='/api/aliexpress/mabang/order')

class MabangOrderController:
    """马帮ERP订单控制器"""
    
    _service = MabangOrderService()
    
    @staticmethod
    @mabang_order_bp.route('/import', methods=['POST'])
    def import_orders():
        """处理订单导入请求
        
        接收上传的Excel文件，验证并导入马帮ERP订单数据。
        
        Returns:
            Response: JSON响应
                成功: {'code': 200, 'msg': '订单导入成功', 'data': {'total': 导入数量, 'skipped': 跳过数量}}
                失败: {'code': 500, 'msg': 错误信息}
                
        Note:
            - 仅支持 .xls 和 .xlsx 格式的文件
            - 文件会被临时保存后自动删除
            - 自动跳过已存在的订单
        """
        try:
            # 检查是否有文件
            if 'file' not in request.files:
                return ResponseHelper.error(msg='没有上传文件')
                
            file = request.files['file']
            
            # 检查文件名
            if file.filename == '':
                return ResponseHelper.error(msg='未选择文件')
                
            # 检查文件扩展名
            if not file.filename.endswith(('.xls', '.xlsx')):
                return ResponseHelper.error(msg='只支持Excel文件')
                
            # 保存文件
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            try:
                # 导入订单
                success, result = MabangOrderController._service.import_orders_from_excel(file_path)
            finally:
                # 确保临时文件被删除
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            if not success:
                return ResponseHelper.error(msg=result)
                
            return ResponseHelper.success(msg='订单导入成功', data=result)
            
        except Exception as e:
            return ResponseHelper.error(msg=f'订单导入失败: {str(e)}')
            
    @staticmethod
    @mabang_order_bp.route('/list', methods=['GET'])
    def list_orders():
        """获取订单列表
        
        支持分页查询马帮ERP订单列表。
        
        Query Parameters:
            page (int): 页码，默认1
            page_size (int): 每页记录数，默认10
            
        Returns:
            Response: JSON响应
                成功: {'code': 200, 'msg': '获取订单列表成功', 'data': [...]}
                失败: {'code': 500, 'msg': 错误信息}
        """
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))
            category = request.args.get('category', '')
            store = request.args.get('store', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            # 构建查询条件
            filters = {}
            if category:
                filters['category'] = category
            if store:
                filters['store'] = store
            if start_date and end_date:
                filters['payment_time'] = (start_date, end_date, 'BETWEEN')
            
            success, result = MabangOrderController._service.list_orders(
                page=page,
                page_size=page_size,
                filters=filters
            )
            
            if not success:
                return ResponseHelper.error(msg=result)
                
            return ResponseHelper.success(msg='获取订单列表成功', data=result)
            
        except Exception as e:
            return ResponseHelper.error(msg=f'获取订单列表失败: {str(e)}')

    @staticmethod
    @mabang_order_bp.route('/import-directory', methods=['POST'])
    def import_orders_from_directory():
        """从目录导入订单数据"""
        try:
            data = request.get_json()
            directory_path = data.get('directory_path')
            category = data.get('category')
            
            if not directory_path:
                return ResponseHelper.error(msg='请指定目录路径')
                
            if not category:
                return ResponseHelper.error(msg='请指定订单类别')
                
            if not os.path.exists(directory_path):
                return ResponseHelper.error(msg='目录不存在')
                
            success, result = MabangOrderController._service.import_orders_from_directory(
                directory_path=directory_path,
                category=category
            )
            
            if not success:
                return ResponseHelper.error(msg=result)
                
            return ResponseHelper.success(msg='批量导入成功', data=result)
            
        except Exception as e:
            return ResponseHelper.error(msg=f'批量导入失败: {str(e)}') 