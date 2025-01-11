import logging.config
import os

# 日志文件路径
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'app.log')

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# 应用日志配置
logging.config.dictConfig(LOGGING_CONFIG) 