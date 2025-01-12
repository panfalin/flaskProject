import logging
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from app.config.mysql_config import MYSQL_CONFIG


class DatabaseManager:
    def __init__(self, config: dict = None):
        # 如果没有传入配置，使用默认配置
        self.config = config if config is not None else MYSQL_CONFIG

    @contextmanager
    def connect(self):
        # 使用上下文管理器确保连接被正确关闭
        connection = pymysql.connect(**self.config, cursorclass=DictCursor)
        try:
            yield connection
        finally:
            connection.close()

    def create(self, table: str, data: dict) -> int:
        # 参数验证
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