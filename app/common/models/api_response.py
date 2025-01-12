from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class ApiResponse:
    code: int = 200
    msg: str = "操作成功"
    total: int = 0
    rows: List[Any] = None
    data: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'code': self.code,
            'msg': self.msg
        }
        
        # 如果有分页数据
        if self.rows is not None:
            result['total'] = self.total
            result['rows'] = self.rows
        # 如果有其他数据
        elif self.data is not None:
            result['data'] = self.data
            
        return result 