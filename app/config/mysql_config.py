# coding: utf-8
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认数据库配置
MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'db': os.getenv('DB_NAME', 'ry-vue'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4'
}
