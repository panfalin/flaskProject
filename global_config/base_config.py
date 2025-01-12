import os


class BaseConfig:
    # 基础配置
    DEBUG = False
    TESTING = False

    # 通用配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 30


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # 开发环境数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DB = 'ry-vue'

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'


class ProductionConfig(BaseConfig):
    # 生产环境数据库配置
    MYSQL_HOST = os.getenv('PROD_DB_HOST', 'prod.database.server')
    MYSQL_PORT = 3306
    MYSQL_USER = os.getenv('PROD_DB_USER', 'prod_user')
    MYSQL_PASSWORD = os.getenv('PROD_DB_PASSWORD', 'prod_password')
    MYSQL_DB = os.getenv('PROD_DB_NAME', 'db_production')

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'

    # 生产环境特定配置
    SQLALCHEMY_POOL_SIZE = 20  # 更大的连接池
    SQLALCHEMY_POOL_TIMEOUT = 60  # 更长的超时时间


class TestingConfig(BaseConfig):
    TESTING = True
    # 测试环境数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'test_user'
    MYSQL_PASSWORD = 'test_password'
    MYSQL_DB = 'db_testing'

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'

    # 测试环境特定配置
    SQLALCHEMY_POOL_SIZE = 5  # 测试环境使用较小的连接池


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
