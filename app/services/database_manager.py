import logging
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor  # 单独导入 DictCursor


# 确保在项目启动时导入 logging_config.py
# import global_config.logging_config


class DatabaseManager:
    def __init__(self, config: dict):
        self.config = config

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
            distinct_columns: str = None  # 新增 distinct_columns 参数
    ) -> list:
        """
        从数据库中读取数据，支持条件查询、分页以及按指定字段使用 DISTINCT。

        :param table: 表名
        :param columns: 查询的列，默认为 '*'
        :param where: 查询条件，字典形式
        :param page: 页码（从 1 开始），可选
        :param page_size: 每页的记录数，可选
        :param distinct_columns: 指定去重的列，若为 None 则不使用 DISTINCT
        :return: 查询结果列表
        """
        where_clause = ''
        values = []

        # 构建 WHERE 条件
        if where:
            conditions = []
            for col, value in where.items():
                if value is None:  # 字段为空的情况
                    conditions.append(f"{col} IS NULL")
                elif isinstance(value, tuple) and value[1].lower() == 'like':  # 模糊查询
                    conditions.append(f"{col} LIKE %s")
                    values.append(f"%{value[0]}%")
                elif isinstance(value, dict) and 'between' in value:  # BETWEEN 查询
                    conditions.append(f"{col} BETWEEN %s AND %s")
                    values.extend(value['between'])
                elif isinstance(value, tuple) and value[1].lower() == '>':  # 大于查询
                    conditions.append(f"{col} > %s")
                    values.append(value[0])
                else:  # 普通的等于查询
                    conditions.append(f"{col} = %s")
                    values.append(value)

            where_clause = ' WHERE ' + ' AND '.join(conditions)

        # 如果需要 DISTINCT，则在 SQL 语句中添加 DISTINCT
        if distinct_columns:
            select_columns = f"SELECT DISTINCT {distinct_columns}"  # 使用指定的列进行 DISTINCT
        else:
            select_columns = f"SELECT {columns}"  # 不使用 DISTINCT

        # 构建 SQL 查询语句
        sql = f"{select_columns} FROM {table}{where_clause}"

        # 如果分页参数存在，则添加 LIMIT 和 OFFSET
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            sql += f" LIMIT %s OFFSET %s"
            values.extend([page_size, offset])

        # 执行 SQL 查询
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
        return cursor.rowcount  # 返回受影响的行数

    def delete(self, table: str, where: dict) -> int:
        where_clause = ' AND '.join(f"{col}=%s" for col in where.keys())
        values = tuple(where.values())

        sql = f"DELETE FROM {table} WHERE {where_clause}"

        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)
                connection.commit()
                logging.info(f"Deleted from {table}, where: {where}")
        return cursor.rowcount  # 返回受影响的行数

    def batch_create(self, table: str, data_list: list) -> bool:
        """
        批量插入数据到指定表

        Args:
            table (str): 表名
            data_list (list): 要插入的数据列表，每个元素都是一个字典

        Returns:
            bool: 插入是否成功
        """
        if not data_list:
            return True

        # 获取第一条数据的键作为列名
        columns = list(data_list[0].keys())

        # 构建SQL语句
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        # 准备批量插入的数据
        values = [tuple(data[col] for col in columns) for data in data_list]

        try:
            with self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(sql, values)
                connection.commit()
            return True
        except Exception as e:
            logging.error(f"批量插入数据时出错: {str(e)}")  # 使用 logging 记录错误
            return False