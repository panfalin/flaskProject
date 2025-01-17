import os
import platform
from pathlib import Path

# 判断操作系统类型
IS_WINDOWS = platform.system() == 'Windows'

# 基础存储路径配置
if IS_WINDOWS:
    BASE_UPLOAD_PATH = 'D:/uploads'  # Windows 系统存储在 D 盘
else:
    BASE_UPLOAD_PATH = '/data/uploads'  # Linux 系统存储在 /data 目录

# 确保基础目录存在
Path(BASE_UPLOAD_PATH).mkdir(parents=True, exist_ok=True)

# 不同类型文件的存储子目录
UPLOAD_FOLDERS = {
    'images': os.path.join(BASE_UPLOAD_PATH, 'images'),
    'documents': os.path.join(BASE_UPLOAD_PATH, 'documents'),
    'mindmaps': os.path.join(BASE_UPLOAD_PATH, 'mindmaps'),  # 思维导图
    'texts': os.path.join(BASE_UPLOAD_PATH, 'texts'),        # 文本文件
    'temp': os.path.join(BASE_UPLOAD_PATH, 'temp'),
}

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {
    'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'},
    'documents': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'},
    'mindmaps': {'xmind', 'mm', 'mmap', 'mindmap'},  # 思维导图文件
    'texts': {'txt', 'md', 'markdown', 'json', 'yml', 'yaml', 'xml', 'ini', 'conf'},  # 文本文件
    'all': {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg',
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'xmind', 'mm', 'mmap', 'mindmap',
        'txt', 'md', 'markdown', 'json', 'yml', 'yaml', 'xml', 'ini', 'conf'
    }
}

# 创建所有上传目录
for folder in UPLOAD_FOLDERS.values():
    Path(folder).mkdir(parents=True, exist_ok=True)

# 最大文件大小（字节）
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 