from app.core.services.db import db

class ProductService:
    """产品服务类"""
    
    def __init__(self):
        self.table = 'mskulist'  # 表名作为实例属性
    
    def get_product_info(self, product_id: int):
        """获取产品信息"""
        try:
            success, results = db.query()\
                .select('id', 'msku', 'product_name')\
                .from_table(self.table)\
                .where(id=product_id)\
                .execute()
                
            if not success:
                return False, results
                
            with db.transaction() as cursor:
                cursor.execute(
                    f"UPDATE {self.table} SET update_time = NOW() WHERE id = %s",
                    (product_id,)
                )
                
            return True, results
            
        except Exception as e:
            return False, str(e)
            
    def create_product(self, product_data: dict):
        """创建新产品"""
        try:
            return db.create(self.table, product_data)
        except Exception as e:
            return False, str(e)
            
    def update_product(self, product_id: int, product_data: dict):
        """更新产品信息"""
        try:
            return db.update(
                self.table,
                data=product_data,
                where={'id': product_id}
            )
        except Exception as e:
            return False, str(e)
            
    def delete_product(self, product_id: int):
        """删除产品"""
        try:
            return db.delete(self.table, {'id': product_id})
        except Exception as e:
            return False, str(e)
            
    def list_products(self, page: int = 1, page_size: int = 10):
        """获取产品列表"""
        try:
            success, results = db.query()\
                .select('id', 'msku', 'product_name', 'created_at')\
                .from_table(self.table)\
                .order_by('created_at', desc=True)\
                .limit(page_size)\
                .offset((page - 1) * page_size)\
                .execute()
                
            return success, results
        except Exception as e:
            return False, str(e) 