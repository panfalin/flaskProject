from flask import Blueprint, request, send_file
import os
from datetime import datetime

from app.core.services.file_service import FileService
from app.common.utils.response_helper import ResponseHelper
from app.core.config.file_storage_config import UPLOAD_FOLDERS, ALLOWED_EXTENSIONS

file_bp = Blueprint('file', __name__)

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    # 打印请求信息
    print("Files:", request.files)
    print("Form:", request.form)
    
    if 'file' not in request.files:
        print("没有找到文件字段，可用的字段:", list(request.files.keys()))
        return ResponseHelper.error('没有文件部分', code=400)
    
    file = request.files['file']
    if file.filename == '':
        return ResponseHelper.error('没有选择文件', code=400)

    # 获取文件类型参数，默认为 documents
    file_type = request.form.get('type', 'documents')
    print("文件类型:", file_type)
    print("文件名:", file.filename)
    
    success, result = FileService.save_file(file, file_type)
    
    if success:
        return ResponseHelper.success(
            msg='文件上传成功',
            data={
                'file_path': result
            }
        )
    else:
        return ResponseHelper.error(msg=result, code=400)

@file_bp.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """文件下载接口"""
    try:
        # 下载接口直接返回文件流，不需要包装响应
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return ResponseHelper.error(msg=f'文件下载失败: {str(e)}', code=404)

@file_bp.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """文件删除接口"""
    success, message = FileService.delete_file(filename)
    if success:
        return ResponseHelper.success(msg=message)
    return ResponseHelper.error(msg=message, code=400)

@file_bp.route('/list/<string:file_type>', methods=['GET'])
def list_files(file_type):
    """
    列出指定类型的文件
    
    Args:
        file_type: 文件类型 (images/documents/temp)
    """
    try:
        # 检查文件类型是否有效
        if file_type not in UPLOAD_FOLDERS:
            return ResponseHelper.error(msg=f"无效的文件类型: {file_type}", code=400)
            
        folder_path = UPLOAD_FOLDERS[file_type]
        if not os.path.exists(folder_path):
            return ResponseHelper.table_data(rows=[], total=0, msg="文件夹为空")
            
        files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):  # 确保是文件而不是子目录
                # 获取文件信息
                file_stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'path': file_path,
                    'size': file_stat.st_size,  # 文件大小（字节）
                    'created_time': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_time': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
                
        return ResponseHelper.table_data(
            rows=files,
            total=len(files),
            msg="获取文件列表成功"
        )
        
    except Exception as e:
        return ResponseHelper.error(msg=f"获取文件列表失败: {str(e)}", code=500)

@file_bp.route('/list', methods=['GET'])
def list_all_files():
    """列出所有类型的文件"""
    try:
        all_files = []
        total_count = 0
        
        for file_type, folder_path in UPLOAD_FOLDERS.items():
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        file_stat = os.stat(file_path)
                        all_files.append({
                            'type': file_type,
                            'name': filename,
                            'path': file_path,
                            'size': file_stat.st_size,
                            'created_time': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                            'modified_time': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                        total_count += 1
                        
        return ResponseHelper.table_data(
            rows=all_files,
            total=total_count,
            msg="获取所有文件列表成功"
        )
        
    except Exception as e:
        return ResponseHelper.error(msg=f"获取文件列表失败: {str(e)}", code=500)

@file_bp.route('/preview/<path:filename>', methods=['GET'])
def preview_file(filename):
    """文件预览接口"""
    try:
        # 检查文件是否存在
        if not os.path.exists(filename):
            return ResponseHelper.error("文件不存在", code=404)
            
        # 获取文件扩展名
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        # 对于图片文件，直接返回
        if ext in ALLOWED_EXTENSIONS['images']:
            return send_file(filename)
            
        # 对于文本文件，读取内容
        if ext in ALLOWED_EXTENSIONS['texts']:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                return ResponseHelper.success(data={'content': content})
            except UnicodeDecodeError:
                return ResponseHelper.error("文件编码不支持", code=400)
                
        return ResponseHelper.error("不支持预览此类型文件", code=400)
        
    except Exception as e:
        return ResponseHelper.error(f"预览失败: {str(e)}", code=500)

@file_bp.route('/batch/delete', methods=['POST'])
def batch_delete_files():
    """批量删除文件"""
    try:
        file_paths = request.json.get('files', [])
        if not file_paths:
            return ResponseHelper.error("未提供文件路径", code=400)
            
        results = []
        for file_path in file_paths:
            success, message = FileService.delete_file(file_path)
            results.append({
                'path': file_path,
                'success': success,
                'message': message
            })
            
        return ResponseHelper.success(
            msg="批量删除完成",
            data={'results': results}
        )
        
    except Exception as e:
        return ResponseHelper.error(f"批量删除失败: {str(e)}", code=500)

@file_bp.route('/batch/upload', methods=['POST'])
def batch_upload_files():
    """批量上传文件"""
    try:
        if 'files[]' not in request.files:
            return ResponseHelper.error("没有文件", code=400)
            
        file_type = request.form.get('type', 'documents')
        files = request.files.getlist('files[]')
        
        results = []
        for file in files:
            if file.filename:
                success, result = FileService.save_file(file, file_type)
                results.append({
                    'filename': file.filename,
                    'success': success,
                    'result': result
                })
                
        return ResponseHelper.success(
            msg="批量上传完成",
            data={'results': results}
        )
        
    except Exception as e:
        return ResponseHelper.error(f"批量上传失败: {str(e)}", code=500)

@file_bp.route('/search', methods=['GET'])
def search_files():
    """搜索文件"""
    try:
        # 获取搜索参数
        keyword = request.args.get('keyword', '')
        file_type = request.args.get('type', 'all')
        min_size = request.args.get('min_size', type=int)
        max_size = request.args.get('max_size', type=int)
        
        results = []
        search_folders = [UPLOAD_FOLDERS[file_type]] if file_type in UPLOAD_FOLDERS else UPLOAD_FOLDERS.values()
        
        for folder in search_folders:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    if keyword.lower() in filename.lower():
                        file_path = os.path.join(folder, filename)
                        if os.path.isfile(file_path):
                            file_stat = os.stat(file_path)
                            # 检查文件大小是否在范围内
                            if (min_size is None or file_stat.st_size >= min_size) and \
                               (max_size is None or file_stat.st_size <= max_size):
                                results.append({
                                    'name': filename,
                                    'path': file_path,
                                    'size': file_stat.st_size,
                                    'created_time': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                                    'modified_time': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                                })
                                
        return ResponseHelper.table_data(
            rows=results,
            total=len(results),
            msg="搜索完成"
        )
        
    except Exception as e:
        return ResponseHelper.error(f"搜索失败: {str(e)}", code=500)

@file_bp.route('/stats', methods=['GET'])
def get_storage_stats():
    """获取存储统计信息"""
    try:
        stats = {
            'total_size': 0,
            'total_files': 0,
            'by_type': {}
        }
        
        for file_type, folder in UPLOAD_FOLDERS.items():
            type_stats = {
                'size': 0,
                'count': 0,
                'extensions': {}
            }
            
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
                        
                        # 更新统计信息
                        type_stats['size'] += file_size
                        type_stats['count'] += 1
                        type_stats['extensions'][ext] = type_stats['extensions'].get(ext, 0) + 1
                        
                        stats['total_size'] += file_size
                        stats['total_files'] += 1
                        
            stats['by_type'][file_type] = type_stats
            
        return ResponseHelper.success(
            msg="获取存储统计信息成功",
            data={
                'stats': stats,
                'readable_total_size': FileService.format_size(stats['total_size'])
            }
        )
        
    except Exception as e:
        return ResponseHelper.error(f"获取统计信息失败: {str(e)}", code=500) 