# 登录页面 URL
FRONTEND_LOGIN_URL = "https://login.aliexpress.com"
BACKEND_LOGIN_URL = "https://login.aliexpress.com/csp_login.htm?return_url=http://csp.aliexpress.com/apps/order/index?spm"

# 登录页面元素选择器
LOGIN_SELECTORS = {
    'username': '//*[@id="loginName"]',
    'password': '//*[@id="password"]',
    'login_button': '//*[@id="root"]/div/main/section[2]/section/section/section/button[1]'
}

# 页面版本选择器配置
PAGE_SELECTORS = {
    'old': {
        'username': '//*[@id="loginName"]',
        'password': '//*[@id="password"]',
        'login_button': '//*[@id="root"]/div/main/section[2]/section/section/section/button[1]'
    },
    'new': {
        'username': '//*[@id="root"]/div/div[2]/div/div[2]/div/div/div[1]/div[1]/div[3]/div[2]/div/span/span[1]/span[1]/input',
        'password': '//*[@id="fm-login-password"]',
        'continue_button': '//*[@id="root"]/div/div[2]/div/div[2]/div/div/div[1]/div[1]/div[3]/div[3]/button',
        'login_button': '//*[@id="root"]/div/div[2]/div/div[2]/div/div/div[1]/div[8]/button'
    }
}

# 滑块验证相关配置
SLIDER_SELECTORS = {
    "error_class": "error-text",
    "iframe_id": "baxia-dialog-content",
    "element_xpath": '//span[@class="nc-lang-cnt"]',
    "handle_xpath": '//*[@id="nc_1_n1z"]',
    "error_loading_class": "errloading",
    "refresh_button_id": "nc_1_refresh1"
}

# Cookie 验证配置
COOKIE_VALIDATION = {
    "required_fields": ['isg', '_m_h5_tk_enc']
}

# 延迟配置（秒）
DELAY_CONFIG = {
    "min_delay": 0.5,  # 最小随机延迟
    "max_delay": 1.5,  # 最大随机延迟
    "slider_min_delay": 0.2,  # 滑块操作最小延迟
    "slider_max_delay": 0.5   # 滑块操作最大延迟
}

