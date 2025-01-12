import random
import time

from chromedriver_py import binary_path  # 使用 chromedriver_py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.config.aliexpress_login_config import (
    FRONTEND_LOGIN_URL,
    SLIDER_SELECTORS, COOKIE_VALIDATION,
    DELAY_CONFIG, PAGE_SELECTORS
)
from app.core.services.database_manager import DatabaseManager


class AliExpressFrontendLoginScraper:

    def __init__(self):
        self.db_manager = DatabaseManager()

    def random_delay(self, min_delay=DELAY_CONFIG['min_delay'], max_delay=DELAY_CONFIG['max_delay']):
        time.sleep(random.uniform(min_delay, max_delay))

    def setup_driver(self):
        try:
            chrome_options = Options()
            # chrome_options.add_argument("--headless")  # 无界面模式
            # chrome_options.add_argument("--no-sandbox")
            # chrome_options.add_argument("--disable-dev-shm-usage")

            # 使用 chromedriver_py 提供的 binary_path
            service = Service(executable_path=binary_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 添加反检测
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                """
            })
            return driver

        except Exception as e:
            # 提取有用的错误信息
            error_msg = str(e)
            if "This version of ChromeDriver only supports Chrome version" in error_msg:
                version_info = error_msg.split("Current browser version is ")[1].split(" ")[0]
                print(f"ChromeDriver 版本不匹配: 当前 Chrome 版本为 {version_info}")
                print("请更新 chromedriver-py 包到匹配的版本:")
                print(f"pip install chromedriver-py=={version_info}")
            else:
                print("初始化 ChromeDriver 失败，请检查:")
                print("1. Chrome 浏览器是否正确安装")
                print("2. chromedriver-py 包是否安装正确")
                print(f"错误信息: {error_msg.split('Stacktrace')[0]}")  # 只显示主要错误信息
            raise

    def solve_slider(self, driver):
        """处理滑块验证"""
        try:
            max_attempts = 3  # 最大尝试次数
            for attempt in range(max_attempts):
                try:
                    # 切换到滑块框架
                    if attempt == 0:  # 第一次尝试
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, SLIDER_SELECTORS['error_class']))
                        )
                        iframe = driver.find_element(By.ID, SLIDER_SELECTORS['iframe_id'])
                        driver.switch_to.frame(iframe)
                    else:  # 后续重试
                        # 检查是否出现错误提示和刷新按钮
                        error_elements = driver.find_elements(By.CLASS_NAME, SLIDER_SELECTORS['error_loading_class'])
                        if error_elements and any(elem.is_displayed() for elem in error_elements):
                            print(f"检测到滑块错误 (尝试 {attempt + 1}/{max_attempts})")
                            # 点击刷新按钮
                            refresh_button = driver.find_element(By.ID, SLIDER_SELECTORS['refresh_button_id'])
                            if refresh_button and refresh_button.is_displayed():
                                refresh_button.click()
                                print("点击刷新按钮")
                                time.sleep(1)  # 等待刷新
                            else:
                                print("未找到刷新按钮")

                    # 等待并操作滑块
                    slider = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, SLIDER_SELECTORS['element_xpath']))
                    )
                    slider_handle = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, SLIDER_SELECTORS['handle_xpath']))
                    )

                    # 执行滑动
                    actions = ActionChains(driver)
                    actions.click_and_hold(slider_handle)
                    actions.move_by_offset(306, 0)  # 直接滑到底
                    self.random_delay(DELAY_CONFIG['slider_min_delay'], DELAY_CONFIG['slider_max_delay'])
                    actions.release().perform()

                    # 等待验证结果
                    time.sleep(2)

                    # 检查是否验证成功
                    if not any(elem.is_displayed() for elem in
                               driver.find_elements(By.CLASS_NAME, SLIDER_SELECTORS['error_loading_class'])):
                        print("滑块验证成功")
                        break
                    else:
                        print("滑块验证失败，将重试")
                        continue

                except Exception as e:
                    print(f"滑块操作出错 (尝试 {attempt + 1}/{max_attempts}): {str(e).split('Stacktrace')[0]}")
                    if attempt < max_attempts - 1:
                        continue
                    raise

            else:
                raise Exception("多次尝试后仍未通过滑块验证")

        except Exception as e:
            print(f"滑块处理时出错: {str(e).split('Stacktrace')[0]}")

        finally:
            driver.switch_to.default_content()  # 确保切回主框架

    def login(self, driver, username, password):
        try:
            initial_url = FRONTEND_LOGIN_URL
            driver.get(initial_url)

            # 检查页面结构
            current_selectors = self.check_page_structure(driver)
            if not current_selectors:
                return None

            # 判断是否是新版本登录界面
            is_new_version = 'continue_button' in current_selectors

            # 输入用户名
            try:
                username_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, current_selectors['username']))
                )
                username_element.clear()
                username_element.send_keys(username)
                print("成功输入用户名")

                # 如果是新版本，需要先点击 continue
                if is_new_version:
                    continue_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, current_selectors['continue_button'])
                        )
                    )
                    self.random_delay()
                    continue_btn.click()
                    print("点击继续按钮")

            except Exception as e:
                print("无法找到用户名输入框或继续按钮")
                print(f"当前页面标题: {driver.title}")
                return None

            # 输入密码
            try:
                password_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, current_selectors['password']))
                )
                password_element.clear()
                password_element.send_keys(password)
                print("成功输入密码")
            except Exception as e:
                print("无法找到密码输入框")
                return None

            # 点击登录按钮并处理可能的滑块验证
            try:
                # 点击登录按钮
                login_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, current_selectors['login_button'])
                    )
                )
                self.random_delay()
                login_btn.click()
                print("成功点击登录按钮")

                # 等待一下，让可能的滑块出现
                time.sleep(2)

                # 处理滑块验证（如果有）
                if len(driver.find_elements(By.CLASS_NAME, SLIDER_SELECTORS['error_class'])) > 0:
                    print("检测到滑块验证")
                    self.solve_slider(driver)
                    # 重新点击登录按钮
                    login_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, current_selectors['login_button'])
                        )
                    )
                    self.random_delay()
                    login_btn.click()
                    print("滑块验证后重新点击登录按钮")

                # 等待页面跳转
                print("等待页面跳转...")
                max_wait_time = 20
                start_time = time.time()
                success_url = "https://www.aliexpress.com/"

                while time.time() - start_time < max_wait_time:
                    current_url = driver.current_url

                    # 检查页面加载状态
                    if driver.execute_script('return document.readyState') != 'complete':
                        print("页面加载中...")
                        time.sleep(1)
                        continue

                    # 检查URL状态
                    if current_url == success_url.lower():
                        print("成功跳转到速卖通主页")
                        return self.get_cookies(driver)  # 获取 cookies
                    elif "login" in current_url:
                        print(f"仍在登录页面: {current_url}")
                        # 检查是否需要重新处理滑块
                        if len(driver.find_elements(By.CLASS_NAME, SLIDER_SELECTORS['error_class'])) > 0:
                            print("检测到新的滑块验证，需要重新验证")
                            self.solve_slider(driver)
                            # 重新点击登录按钮
                            login_btn = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, current_selectors['login_button'])
                                )
                            )
                            self.random_delay()
                            login_btn.click()
                            print("滑块验证后重新点击登录按钮")
                    elif "aliexpress.com" in current_url:
                        print(f"在速卖通其他页面: {current_url}")
                        driver.get(success_url)

                    time.sleep(1)

                print(f"登录超时，最后的URL: {driver.current_url}")
                return None

            except Exception as e:
                print(f"登录过程出错: {str(e)}")
                return None

        except Exception as e:
            print(f"登录过程中发生错误: {str(e)}")
            return None

    def get_cookies(self, driver):
        """获取并验证 cookies"""
        try:
            print("等待 cookie 设置完成...")
            time.sleep(5)

            max_retries = 3
            for retry in range(max_retries):
                ae_cookie = driver.get_cookies()
                if not ae_cookie:
                    print(f"尝试 {retry + 1}/{max_retries}: 未获取到 cookies")
                    time.sleep(2)
                    continue

                cookie_string = "; ".join([f"{item['name']}={item['value']}" for item in ae_cookie])
                print(f"获取到 {len(ae_cookie)} 个 cookies")

                # 验证必需的 cookie 字段
                required_cookies = COOKIE_VALIDATION['required_fields']
                found_cookies = [c['name'] for c in ae_cookie]
                missing_cookies = [req for req in required_cookies if req not in found_cookies]

                if missing_cookies:
                    print(f"缺少必需的 cookies: {missing_cookies}")
                    if retry < max_retries - 1:
                        print("等待后重试...")
                        time.sleep(2)
                        continue
                    return None

                print("所有必需的 cookie 都已获取")
                print(f"Cookie 字段: {', '.join(found_cookies)}")
                return cookie_string

            print("多次尝试后仍未获取到有效的 cookies")
            return None

        except Exception as e:
            print(f"获取 cookies 时出错: {str(e)}")
            return None

    def get_account_cookie_str(self, account):
        username = account.get("username")
        driver = None
        try:
            driver = self.setup_driver()
            password = account['password']
            cookie_str = self.login(driver=driver, username=username, password=password)
            if cookie_str:
                self.db_manager.update('sys_cookie',
                                       data={"cooking_context": cookie_str},
                                       where={"project": "aliexpress", "username": username})
            return cookie_str
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"关闭浏览器时出错: {str(e)}")

    def check_page_structure(self, driver):
        """检查页面结构并返回当前使用的选择器"""
        try:
            print(f"当前页面 URL: {driver.current_url}")
            print(f"当前页面标题: {driver.title}")

            # 保存页面源码以供分析
            page_source_path = "page_structure.html"
            with open(page_source_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"页面源码已保存到: {page_source_path}")

            # 检查每个选择器是否存在
            for version, selector_set in PAGE_SELECTORS.items():
                elements_found = []
                for name, xpath in selector_set.items():
                    try:
                        element = driver.find_element(By.XPATH, xpath)
                        if element.is_displayed():
                            elements_found.append(name)
                    except:
                        continue

                if len(elements_found) >= 2:  # 如果找到至少两个元素，认为是当前版本
                    print(f"检测到 {version} 版本的页面结构")
                    return selector_set

            # 如果都没找到，打印所有可见的输入框和按钮
            print("\n=== 可见元素分析 ===")
            print("输入框:")
            for input_elem in driver.find_elements(By.TAG_NAME, "input"):
                if input_elem.is_displayed():
                    print(f"ID: {input_elem.get_attribute('id')}")
                    print(f"Name: {input_elem.get_attribute('name')}")
                    print(f"XPath: {self.get_element_xpath(input_elem, driver)}")
                    print("---")

            print("\n按钮:")
            for button in driver.find_elements(By.TAG_NAME, "button"):
                if button.is_displayed():
                    print(f"Text: {button.text}")
                    print(f"XPath: {self.get_element_xpath(button, driver)}")
                    print("---")

            raise Exception("无法识别的页面结构")

        except Exception as e:
            print(f"页面结构检查失败: {str(e)}")
            return None

    def get_element_xpath(self, element, driver):
        """获取元素的 XPath"""
        try:
            return driver.execute_script("""
                function getElementXPath(element) {
                    if (element && element.id)
                        return `//*[@id="${element.id}"]`;
                        
                    const paths = [];
                    while (element) {
                        let index = 1;
                        for (let sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
                            if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === element.tagName) {
                                index++;
                            }
                        }
                        const tagName = element.tagName.toLowerCase();
                        paths.unshift(`${tagName}[${index}]`);
                        element = element.parentNode;
                    }
                    return '/' + paths.join('/');
                }
                return getElementXPath(arguments[0]);
            """, element)
        except:
            return "无法获取 XPath"
