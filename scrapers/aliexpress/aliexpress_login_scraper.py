import random
import time

from chromedriver_py import binary_path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.config.aliexpress_login_config import BACKEND_LOGIN_URL


class AliExpressLoginScraper:
    def random_delay(self, min_delay=0.5, max_delay=1.5):
        time.sleep(random.uniform(min_delay, max_delay))

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")
        service = Service(binary_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
            """
        })
        driver.set_window_position(1920, 0)
        return driver

    def login(self, driver, username, password):
        try:
            driver.get(BACKEND_LOGIN_URL)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="loginName"]'))
            )
            username_element = driver.find_element(By.XPATH, '//*[@id="loginName"]')
            username_element.send_keys(username)
            password_element = driver.find_element(By.XPATH, '//*[@id="password"]')
            password_element.send_keys(password)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="root"]/div/main/section[2]/section/section/section/button[1]'))
            )
            time.sleep(2)
            login_btn = driver.find_element(By.XPATH,
                                            '//*[@id="root"]/div/main/section[2]/section/section/section/button[1]')
            if login_btn:
                login_btn.click()
                print("点击登录按钮成功！")
            else:
                print("登录按钮未选中")
            time.sleep(3)
            try:
                check_btn = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="ae-layout-root"]/section[2]/div[1]/div/div/ul/li[3]/ul/li[2]/div/span/a'))
                )
                check_btn.click()
            except Exception as e:
                print(e)
            ae_cookie = driver.get_cookies()
            cookie_string = "; ".join([f"{item['name']}={item['value']}" for item in ae_cookie])
            return cookie_string
        except Exception as e:
            print(f"登录过程中发生错误: {e}")
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
                                       data={"cooking_context": cookie_str, "expired_time": time.time().__add__()},
                                       where={"project": "aliexpress", "username": username})
            return cookie_str
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"关闭浏览器时出错: {str(e)}")
