from flask import Blueprint, request, jsonify, send_file
from app.core.services.file_service import FileService

file_bp = Blueprint('file', __name__)

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件部分'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400

    # 获取文件类型参数，默认为 documents
    file_type = request.form.get('type', 'documents')
    
    success, result = FileService.save_file(file, file_type)
    
    if success:
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'file_path': result
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': result
        }), 400

@file_bp.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """文件下载接口"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文件下载失败: {str(e)}'
        }), 404

@file_bp.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """文件删除接口"""
    success, message = FileService.delete_file(filename)
    return jsonify({
        'success': success,
        'message': message
    }), 200 if success else 400 