import logging
from contextlib import contextmanager
from typing import Optional, List, Any

import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB

from app.config.mysql_config import MYSQL_CONFIG


class QueryBuilder:
    """SQL 查询构建器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager  # 保存 DatabaseManager 实例
        self.table = None
        self.select_columns = ['*']
        self.where_conditions = []
        self.where_values = []
        self.order_by_columns = []
        self.group_by_columns = []
        self.limit_count = None
        self.offset_count = None
        self.join_clauses = []
        
    def select(self, *columns) -> 'QueryBuilder':
        """选择要查询的列"""
        if columns:
            self.select_columns = list(columns)
        return self
    
    def from_table(self, table: str) -> 'QueryBuilder':
        """设置查询的表名"""
        self.table = table
        return self
    
    def where(self, **conditions) -> 'QueryBuilder':
        """添加 WHERE 条件"""
        for column, value in conditions.items():
            if isinstance(value, tuple) and len(value) == 2:
                # 处理特殊操作符，如 LIKE, >, <
                operator = value[1].upper()
                if operator == 'LIKE':
                    self.where_conditions.append(f"{column} LIKE %s")
                    self.where_values.append(f"%{value[0]}%")
                else:
                    self.where_conditions.append(f"{column} {operator} %s")
                    self.where_values.append(value[0])
            else:
                self.where_conditions.append(f"{column} = %s")
                self.where_values.append(value)
        return self
    
    def order_by(self, column: str, desc: bool = False) -> 'QueryBuilder':
        """添加排序条件"""
        self.order_by_columns.append(f"{column} {'DESC' if desc else 'ASC'}")
        return self
    
    def group_by(self, *columns) -> 'QueryBuilder':
        """添加分组条件"""
        self.group_by_columns.extend(columns)
        return self
    
    def limit(self, count: int, offset: int = None) -> 'QueryBuilder':
        """添加限制条件"""
        self.limit_count = count
        self.offset_count = offset
        return self
    
    def join(self, table: str, on: dict, join_type: str = 'INNER') -> 'QueryBuilder':
        """添加连接查询"""
        conditions = []
        for left, right in on.items():
            conditions.append(f"{left} = {right}")
        join_clause = f"{join_type} JOIN {table} ON {' AND '.join(conditions)}"
        self.join_clauses.append(join_clause)
        return self
    
    def offset(self, offset_value: int) -> 'QueryBuilder':
        """
        设置查询的偏移量
        
        Args:
            offset_value: 偏移的记录数
            
        Returns:
            QueryBuilder: 查询构建器实例，支持链式调用
        """
        self.offset_count = offset_value
        return self
    
    def build(self) -> tuple:
        """构建 SQL 语句"""
        if not self.table:
            raise ValueError("No table specified")
            
        sql_parts = [
            f"SELECT {', '.join(self.select_columns)}",
            f"FROM {self.table}"
        ]
        
        # 添加 JOIN 子句
        if self.join_clauses:
            sql_parts.extend(self.join_clauses)
        
        # 添加 WHERE 子句
        if self.where_conditions:
            sql_parts.append("WHERE " + " AND ".join(self.where_conditions))
        
        # 添加 GROUP BY 子句
        if self.group_by_columns:
            sql_parts.append("GROUP BY " + ", ".join(self.group_by_columns))
        
        # 添加 ORDER BY 子句
        if self.order_by_columns:
            sql_parts.append("ORDER BY " + ", ".join(self.order_by_columns))
        
        # 添加 LIMIT 和 OFFSET
        if self.limit_count is not None:
            sql_parts.append(f"LIMIT {self.limit_count}")
            if self.offset_count is not None:
                sql_parts.append(f"OFFSET {self.offset_count}")
        
        return " ".join(sql_parts), tuple(self.where_values)

    def execute(self) -> tuple:
        """
        执行构建的查询
        
        Returns:
            tuple: (是否成功, 结果/错误信息)
        """
        try:
            sql, params = self.build()
            return self.db_manager.execute_sql(sql, params)
        except Exception as e:
            return False, str(e)


class DatabaseManager:
    """数据库管理器类，提供 MySQL 数据库操作的封装"""
    
    _instance = None
    _pool = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: dict = None):
        """初始化连接池"""
        if DatabaseManager._pool is None:
            self.config = config if config is not None else MYSQL_CONFIG
            DatabaseManager._pool = PooledDB(
                creator=pymysql,
                maxconnections=10,  # 最大连接数
                mincached=2,        # 初始连接数
                maxcached=5,        # 最大空闲连接数
                maxshared=3,        # 最大共享连接数
                blocking=True,      # 连接池满时是否阻塞
                maxusage=None,      # 单个连接最大复用次数
                setsession=[],      # 开始会话前执行的命令
                cursorclass=DictCursor,
                **self.config
            )
    
    def get_connection(self):
        """获取数据库连接"""
        return DatabaseManager._pool.connection()
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        Usage:
            with db.transaction() as cursor:
                cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
                cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Transaction failed: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def query(self) -> QueryBuilder:
        """
        获取查询构建器
        
        Returns:
            QueryBuilder: 查询构建器实例
            
        Usage:
            results = db.query()
                       .select('id', 'name')
                       .from_table('users')
                       .where(status='active')
                       .order_by('created_at', desc=True)
                       .limit(10)
                       .execute()
        """
        return QueryBuilder(self)  # 传入 self 作为 db_manager
    
    def execute_builder(self, builder: QueryBuilder) -> List[dict]:
        """执行查询构建器生成的查询"""
        sql, params = builder.build()
        return self.execute_sql(sql, params)[1]

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

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                conn.commit()
                logging.info(f"Inserted data into {table}: {data}")
                return cursor.rowcount
        finally:
            conn.close()

    def read(
            self,
            table: str,
            columns: str = '*',
            where: dict = None,
            page: int = None,
            page_size: int = None,
            distinct_columns: str = None
    ) -> list:
        """从数据库读取数据"""
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

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(values))
                result = cursor.fetchall()
                logging.info(
                    f"Read from {table}, columns: {columns}, where: {where}, page: {page}, page_size: {page_size}, distinct_columns: {distinct_columns}"
                )
                return result
        finally:
            conn.close()

    def update(self, table: str, data: dict, where: dict) -> int:
        """更新数据库记录"""
        set_clause = ', '.join(f"{col}=%s" for col in data.keys())
        where_clause = ' AND '.join(f"{col}=%s" for col in where.keys())
        values = tuple(data.values()) + tuple(where.values())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                conn.commit()
                logging.info(f"Updated {table} with data: {data}, where: {where}")
                return cursor.rowcount
        finally:
            conn.close()

    def delete(self, table: str, where: dict) -> int:
        """删除数据库记录"""
        where_clause = ' AND '.join(f"{col}=%s" for col in where.keys())
        values = tuple(where.values())
        sql = f"DELETE FROM {table} WHERE {where_clause}"

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                conn.commit()
                logging.info(f"Deleted from {table}, where: {where}")
                return cursor.rowcount
        finally:
            conn.close()

    def batch_create(self, table: str, data_list: list) -> bool:
        """批量插入数据"""
        if not data_list:
            return True

        columns = list(data_list[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        values = [tuple(data[col] for col in columns) for data in data_list]

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.executemany(sql, values)
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"批量插入数据时出错: {str(e)}")
            return False
        finally:
            conn.close()

    def execute_sql(self, sql: str, params: tuple = None, fetch: bool = True) -> tuple:
        """执行自定义 SQL 语句"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                
                if fetch:
                    results = cursor.fetchall()
                    logging.info(f"执行 SELECT 语句: {sql}, 获取到 {len(results)} 条记录")
                    return True, results
                else:
                    conn.commit()
                    affected_rows = cursor.rowcount
                    logging.info(f"执行 SQL: {sql}, 影响 {affected_rows} 行")
                    return True, affected_rows
                    
        except Exception as e:
            error_msg = str(e)
            logging.error(f"执行 SQL 出错: {sql}, 错误: {error_msg}")
            return False, error_msg
        finally:
            conn.close()

    def warm_up(self):
        """预热连接池"""
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            connection.close()
            logging.info("数据库连接池预热成功")
        except Exception as e:
            logging.error(f"数据库连接池预热失败: {str(e)}")
            raise 