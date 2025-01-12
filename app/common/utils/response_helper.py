from typing import Any, List, Optional, Union
from flask import jsonify

from app.common.models.api_response import ApiResponse


class ResponseHelper:
    @staticmethod
    def success(
            msg: str = "操作成功",
            data: Any = None,
            rows: List[Any] = None,
            total: int = 0
    ):
        """
        成功响应
        
        Args:
            msg: 成功消息
            data: 响应数据（非分页数据）
            rows: 分页数据列表
            total: 分页数据总数
        """
        response = ApiResponse(
            code=200,
            msg=msg,
            data=data,
            rows=rows,
            total=total
        )
        return jsonify(response.to_dict())

    @staticmethod
    def error(
            msg: str = "操作失败",
            code: int = 500,
            data: Any = None
    ):
        """
        错误响应
        
        Args:
            msg: 错误消息
            code: 错误码
            data: 错误详细信息
        """
        response = ApiResponse(
            code=code,
            msg=msg,
            data=data
        )
        return jsonify(response.to_dict())

    @staticmethod
    def table_data(
            rows: List[Any],
            total: int,
            msg: str = "查询成功"
    ):
        """
        表格数据响应
        
        Args:
            rows: 数据列表
            total: 总数
            msg: 消息
        """
        response = ApiResponse(
            code=200,
            msg=msg,
            rows=rows,
            total=total
        )
        return jsonify(response.to_dict()) 