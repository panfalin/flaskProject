import logging
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from app.config.mysql_config import MYSQL_CONFIG


class DatabaseManager:
    """
    数据库管理器类，提供 MySQL 数据库操作的封装
    
    主要功能：
    1. 基础 CRUD 操作
       - create: 插入单条记录
       - read: 查询数据，支持条件查询和分页
       - update: 更新记录
       - delete: 删除记录
    2. 批量操作
       - batch_create: 批量插入数据
    3. 自定义 SQL 执行
       - execute_sql: 执行自定义 SQL 语句
       
    特点：
    1. 使用上下文管理器自动管理数据库连接
    2. 支持参数化查询，防止 SQL 注入
    3. 支持多种查询条件（等值、LIKE、范围、大于）
    4. 详细的日志记录
    5. 统一的错误处理
    
    Example:
        db = DatabaseManager()
        
        # 基础查询
        users = db.read('users', where={'status': 'active'})
        
        # 分页查询
        page_users = db.read('users', page=1, page_size=10)
        
        # 自定义 SQL
        success, results = db.execute_sql(
            "SELECT * FROM users WHERE age > %s",
            params=(18,)
        )
    """

    def __init__(self, config: dict = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置字典，包含 host, user, password, db 等信息
                   如果为 None，则使用默认配置
        """
        self.config = config if config is not None else MYSQL_CONFIG

    @contextmanager
    def connect(self):
        """
        创建数据库连接的上下文管理器
        
        Returns:
            pymysql.Connection: 数据库连接对象
            
        Usage:
            with self.connect() as connection:
                # 使用连接进行操作
        """
        connection = pymysql.connect(**self.config, cursorclass=DictCursor)
        try:
            yield connection
        finally:
            connection.close()

    def create(self, table: str, data: dict) -> int:
        """
        向指定表插入一条数据
        
        Args:
            table: 表名
            data: 要插入的数据字典，键为列名，值为对应的值
            
        Returns:
            int: 受影响的行数
            
        Raises:
            ValueError: 如果 data 不是字典类型
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())

        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                connection.commit()
                logging.info(f"Inserted data into {table}: {data}")
        return cursor.rowcount  # 返回受影响的行数

    def read(
            self,
            table: str,
            columns: str = '*',
            where: dict = None,
            page: int = None,
            page_size: int = None,
            distinct_columns: str = None
    ) -> list:
        """
        从数据库读取数据
        
        Args:
            table: 表名
            columns: 要查询的列名，默认为 '*'
            where: 查询条件字典，支持多种查询方式：
                   - 普通等值查询: {'column': value}
                   - LIKE 查询: {'column': (value, 'like')}
                   - 范围查询: {'column': {'between': [value1, value2]}}
                   - 大于查询: {'column': (value, '>')}
            page: 页码，用于分页查询
            page_size: 每页记录数
            distinct_columns: 需要去重的列名
            
        Returns:
            list: 查询结果列表，每个元素为一个字典
        """
        where_clause = ''
        values = []

        if where:
            conditions = []
            for col, value in where.items():
                if value is None:
                    conditions.append(f"{col} IS NULL")
                elif isinstance(value, tuple) and value[1].lower() == 'like':
                    conditions.append(f"{col} LIKE %s")
                    values.append(f"%{value[0]}%")
                elif isinstance(value, dict) and 'between' in value:
                    conditions.append(f"{col} BETWEEN %s AND %s")
                    values.extend(value['between'])
                elif isinstance(value, tuple) and value[1].lower() == '>':
                    conditions.append(f"{col} > %s")
                    values.append(value[0])
                else:
                    conditions.append(f"{col} = %s")
                    values.append(value)

            where_clause = ' WHERE ' + ' AND '.join(conditions)

        if distinct_columns:
            select_columns = f"SELECT DISTINCT {distinct_columns}"
        else:
            select_columns = f"SELECT {columns}"

        sql = f"{select_columns} FROM {table}{where_clause}"

        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            sql += f" LIMIT %s OFFSET %s"
            values.extend([page_size, offset])

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(values))
                result = cursor.fetchall()
                logging.info(
                    f"Read from {table}, columns: {columns}, where: {where}, page: {page}, page_size: {page_size}, distinct_columns: {distinct_columns}"
                )

        return result

    def update(self, table: str, data: dict, where: dict) -> int:
        """
        更新数据库记录
        
        Args:
            table: 表名
            data: 要更新的数据字典，键为列名，值为新的值
            where: 更新条件字典，指定要更新哪些记录
            
        Returns:
            int: 受影响的行数
        """
        set_clause = ', '.join(f"{col}=%s" for col in data.keys())
        where_clause = ' AND '.join(f"{col}=%s" for col in where.keys())
        values = tuple(data.values()) + tuple(where.values())

        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                connection.commit()
                logging.info(f"Updated {table} with data: {data}, where: {where}")
        return cursor.rowcount

    def delete(self, table: str, where: dict) -> int:
        """
        删除数据库记录
        
        Args:
            table: 表名
            where: 删除条件字典，指定要删除哪些记录
            
        Returns:
            int: 受影响的行数
        """
        where_clause = ' AND '.join(f"{col}=%s" for col in where.keys())
        values = tuple(where.values())

        sql = f"DELETE FROM {table} WHERE {where_clause}"

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                connection.commit()
                logging.info(f"Deleted from {table}, where: {where}")
        return cursor.rowcount

    def batch_create(self, table: str, data_list: list) -> bool:
        """
        批量插入数据
        
        Args:
            table: 表名
            data_list: 要插入的数据列表，每个元素为一个字典
                      所有字典必须具有相同的键
            
        Returns:
            bool: 插入是否成功
            
        Note:
            - 如果 data_list 为空，直接返回 True
            - 所有记录必须具有相同的字段结构
        """
        if not data_list:
            return True

        columns = list(data_list[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        values = [tuple(data[col] for col in columns) for data in data_list]

        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(sql, values)
                connection.commit()
            return True
        except Exception as e:
            logging.error(f"批量插入数据时出错: {str(e)}")
            return False 

    def execute_sql(self, sql: str, params: tuple = None, fetch: bool = True) -> tuple:
        """
        执行自定义 SQL 语句
        
        Args:
            sql: SQL 语句
            params: SQL 参数，用于预处理语句，防止 SQL 注入
            fetch: 是否获取结果，True 表示 SELECT 语句，False 表示 UPDATE/INSERT/DELETE 等
            
        Returns:
            tuple: (是否成功, 结果/错误信息)
                - SELECT 语句返回 (True, results)
                - 其他语句返回 (True, affected_rows)
                - 出错时返回 (False, error_message)
                
        Example:
            # SELECT 查询
            success, results = db.execute_sql(
                "SELECT * FROM users WHERE age > %s",
                params=(18,)
            )
            
            # UPDATE 操作
            success, affected = db.execute_sql(
                "UPDATE users SET status = %s WHERE id = %s",
                params=('active', 1),
                fetch=False
            )
        """
        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    # 执行 SQL
                    cursor.execute(sql, params)
                    
                    if fetch:
                        # SELECT 语句
                        results = cursor.fetchall()
                        logging.info(f"执行 SELECT 语句: {sql}, 参数: {params}, 获取到 {len(results)} 条记录")
                        return True, results
                    else:
                        # 非 SELECT 语句
                        connection.commit()
                        affected_rows = cursor.rowcount
                        logging.info(f"执行 SQL: {sql}, 参数: {params}, 影响 {affected_rows} 行")
                        return True, affected_rows
                        
        except Exception as e:
            error_msg = str(e)
            logging.error(f"执行 SQL 出错: {sql}, 参数: {params}, 错误: {error_msg}")
            return False, error_msg 