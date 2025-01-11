import os

from app import create_app

# 从环境变量获取运行模式
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

# 导入日志配置

if __name__ == '__main__':
    # 只在开发环境启用调试模式
    debug = config_name == 'development'
    app.run(debug=debug)
