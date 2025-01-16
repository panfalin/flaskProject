from app.core.services.db import db
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import re
from decimal import Decimal
import os
import math


class MabangOrderService:
    """马帮ERP订单服务类"""

    # 订单类别常量
    class Category:
        """订单类别枚举"""
        FULL_WAREHOUSE = 'full_warehouse'  # 全托管-仓发
        FULL_JIT = 'full_jit'  # 全托管-JIT
        POP = 'pop'  # POP-自发
        HALF_JIT = 'half_jit'  # 半托管-JIT
        HALF_WAREHOUSE = 'half_warehouse'  # 半托管-仓发

        @classmethod
        def get_all_categories(cls) -> List[str]:
            """获取所有类别"""
            return [
                cls.FULL_WAREHOUSE,
                cls.FULL_JIT,
                cls.POP,
                cls.HALF_JIT,
                cls.HALF_WAREHOUSE
            ]

    def __init__(self):
        self.table = 'mabang_erp_order_list'
        # 文件名与订单类别的映射规则
        self.category_patterns = {
            # 全托管-仓发
            r'(全托管|全托|full).*?(仓发|warehouse)': self.Category.FULL_WAREHOUSE,
            # 全托管-JIT
            r'(全托管|全托|full).*?(jit|即时|及时)': self.Category.FULL_JIT,
            # POP-自发
            r'(pop|自发)': self.Category.POP,
            # 半托管-JIT
            r'(半托管|半托|half).*?(jit|即时|及时)': self.Category.HALF_JIT,
            # 半托管-仓发
            r'(半托管|半托|half).*?(仓发|warehouse)': self.Category.HALF_WAREHOUSE
        }

        # 默认类别映射
        self.default_category_patterns = {
            r'全托管|全托|full': self.Category.FULL_WAREHOUSE,
            r'半托管|半托|half': self.Category.HALF_WAREHOUSE,
            r'pop': self.Category.POP
        }

        # Excel字段映射
        self.field_mapping = {
            '订单编号': 'order_id',
            '交易编号': 'transaction_id',
            '订单核算金额（原始货币）': 'original_amount',
            '订单核算金额（人民币）': 'rmb_amount',
            '付款时间': 'payment_time',
            'SKU': 'sku',
            '商品数量': 'quantity',
            '订单利润': 'order_profit',
            '商品状态': 'product_status',
            '店铺名': 'store',
            '平台订单状态': 'platform_status',
            '统一成本价': 'uniform_cost_price',
            '商品单个成本': 'unit_cost',
            'SKU总数量': 'sku_quantity',
            'SKU明细': 'sku_details',
            '重量': 'weight',
            '国家': 'country',
            '运费收入': 'shipping_revenue',
            '实际运费': 'actual_shipping',
            '订单总金额': 'total_order_amount',
            '订单利润率': 'order_profit_rate',
            '平台交易费(人民币)': 'platform_fee_rmb',
            '广告费(人民币)': 'ad_cost_rmb',
            'VAT税费（人民币）': 'vat_fee_rmb',
            '商品总重量': 'total_product_weight',
            '商品库存': 'stock_quantity',
            'SKU图片链接': 'sku_image_url',
            '商品中文名称': 'product_name_cn',
            '商品英文名称': 'product_name_en'
        }

        # 字段类型映射
        self.field_types = {
            'decimal_fields': [
                'original_amount', 'rmb_amount', 'order_profit',
                'uniform_cost_price', 'unit_cost', 'weight',
                'shipping_revenue', 'actual_shipping', 'total_order_amount',
                'platform_fee_rmb', 'ad_cost_rmb', 'vat_fee_rmb',
                'total_product_weight'
            ],
            'int_fields': ['quantity', 'sku_quantity', 'stock_quantity'],
            'special_fields': {
                'order_profit_rate': self._clean_profit_rate,
                'country': self._handle_nan
            }
        }

    def _get_category_from_filename(self, file_path: str) -> Tuple[bool, str]:
        """从文件名判断订单类别
        
        Returns:
            Tuple[bool, str]: (是否成功, 类别/错误信息)
        """
        filename = os.path.basename(file_path).lower()

        # 优先匹配详细类别
        for pattern, category in self.category_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                return True, category

        # 尝试匹配默认类别
        for pattern, category in self.default_category_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                return True, category

        return False, f"无法从文件名'{filename}'判断订单类别，请确保文件名包含类别信息"

    def _process_row_data(self, row_data: Dict, category: str) -> Optional[Dict]:
        """处理单行数据"""
        try:
            # 跳过PON开头的交易编号
            transaction_id = str(row_data.get('交易编号', ''))
            if transaction_id.startswith('PON'):
                return None

            # 处理必要字段
            order_id = row_data.get('订单编号')
            if not order_id:
                return None

            # 使用字段映射转换数据
            processed_data = {'category': category[1] if isinstance(category, tuple) else category}

            for excel_field, db_field in self.field_mapping.items():
                value = row_data.get(excel_field)

                # 处理 NaN 值
                if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                    processed_data[db_field] = None
                    continue

                # 根据字段类型进行转换
                if db_field in self.field_types['decimal_fields']:
                    processed_value = self._get_decimal(value)
                    processed_data[db_field] = None if pd.isna(processed_value) else processed_value
                elif db_field in self.field_types['int_fields']:
                    processed_value = self._get_int(value)
                    processed_data[db_field] = None if pd.isna(processed_value) else processed_value
                elif db_field in self.field_types['special_fields']:
                    processed_value = self.field_types['special_fields'][db_field](value)
                    processed_data[db_field] = None if pd.isna(processed_value) else processed_value
                else:
                    # 处理字符串类型
                    if isinstance(value, str):
                        processed_data[db_field] = value.strip() if value.strip() else None
                    else:
                        processed_data[db_field] = str(value) if value is not None else None

            # 最后一次检查确保没有 NaN 值
            for key, value in processed_data.items():
                if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                    processed_data[key] = None

            return processed_data

        except Exception as e:
            print(f"处理数据出错: {str(e)}")
            return None

    def _clean_order_data(self, data):
        """清理订单数据，处理特殊值
        
        Args:
            data (dict): 原始订单数据
            
        Returns:
            dict: 清理后的数据
        """
        cleaned = {}
        for key, value in data.items():
            # 处理 NaN 值
            if isinstance(value, float) and math.isnan(value):
                cleaned[key] = None
            # 处理其他数值类型
            elif isinstance(value, (int, float)):
                cleaned[key] = value
            # 处理字符串类型
            elif isinstance(value, str):
                cleaned[key] = value.strip() if value else None
            else:
                cleaned[key] = value
        return cleaned

    def import_orders_from_excel(self, file_path: str) -> tuple:
        """从Excel文件导入订单数据"""
        try:
            # 从文件名判断类别
            success, category = self._get_category_from_filename(file_path)
            if not success:
                return False, category  # category 此时包含错误信息
            
            # 确保 category 是字符串
            if isinstance(category, tuple):
                category = category[1]
            
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            # 处理每一行数据
            success_count = 0
            error_count = 0
            error_msgs = []
            
            for _, row in df.iterrows():
                try:
                    # 转换为字典并处理数据
                    order_data = self._process_row_data(row.to_dict(), category)
                    if not order_data:
                        continue
                    
                    # 不需要再次清理数据，因为 _process_row_data 已经处理过了
                    # 删除这行: order_data = self._clean_order_data(order_data)
                    
                    # 保存到数据库
                    success = db.create(self.table, data=order_data)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        error_msgs.append(f"保存失败: {order_data.get('order_id')}")
                        
                except Exception as e:
                    error_count += 1
                    error_msgs.append(str(e))
            
            return True, {
                'total': len(df),
                'success': success_count,
                'error': error_count,
                'error_msgs': error_msgs[:10]  # 只返回前10条错误信息
            }
            
        except Exception as e:
            return False, f'导入失败: {str(e)}'

    @staticmethod
    def _get_decimal(value: Any) -> Optional[Decimal]:
        """转换为Decimal"""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            if not value:
                return None
        try:
            return Decimal(str(value))
        except:
            return None

    @staticmethod
    def _get_int(value: Any) -> Optional[int]:
        """转换为整数"""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
                if not value:
                    return None
            return int(float(value))
        except:
            return None

    @staticmethod
    def _handle_nan(value: Any) -> Optional[Any]:
        """处理NaN值"""
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    @staticmethod
    def _clean_profit_rate(rate: Any) -> Optional[Decimal]:
        """清理利润率"""
        if not rate:
            return None
        if isinstance(rate, str):
            rate = rate.replace('%', '').strip()
        try:
            return Decimal(str(rate)) / Decimal('100')
        except:
            return None
