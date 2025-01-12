import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from flask import send_file

from app.core.config.file_storage_config import UPLOAD_FOLDERS, ALLOWED_EXTENSIONS


class FileService:
    @staticmethod
    def allowed_file(filename: str, file_type: str = 'all') -> bool:
        """检查文件类型是否允许"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """生成唯一的文件名"""
        # 获取文件扩展名
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        # 生成带时间戳的唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4().hex[:8])
        return f"{timestamp}_{unique_id}.{ext}"

    @staticmethod
    def save_file(file, file_type: str = 'documents') -> Tuple[bool, str]:
        """
        保存上传的文件
        
        Args:
            file: FileStorage对象
            file_type: 文件类型（对应UPLOAD_FOLDERS中的键）
            
        Returns:
            Tuple[bool, str]: (是否成功, 成功则返回文件路径，失败则返回错误信息)
        """
        if file and file.filename:
            if not FileService.allowed_file(file.filename, file_type):
                return False, "文件类型不允许"

            filename = secure_filename(file.filename)
            unique_filename = FileService.generate_unique_filename(filename)
            
            # 获取保存路径
            save_path = UPLOAD_FOLDERS.get(file_type)
            if not save_path:
                return False, "无效的文件类型"

            # 确保目录存在
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            # 完整的文件保存路径
            file_path = os.path.join(save_path, unique_filename)
            
            try:
                file.save(file_path)
                return True, file_path
            except Exception as e:
                return False, f"文件保存失败: {str(e)}"
        return False, "没有文件或文件名为空"

    @staticmethod
    def get_file(file_path: str) -> Optional[str]:
        """
        获取文件的完整路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 文件的完整路径，如果文件不存在则返回 None
        """
        if os.path.exists(file_path):
            return file_path
        return None

    @staticmethod
    def delete_file(file_path: str) -> Tuple[bool, str]:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 成功或失败的消息)
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, "文件删除成功"
            return False, "文件不存在"
        except Exception as e:
            return False, f"文件删除失败: {str(e)}" 