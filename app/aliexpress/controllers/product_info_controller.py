from flask import Blueprint, jsonify

from app.aliexpress.services.aliexpress_product_info_service import AliexpressProductInfoService
from scrapers.aliexpress.aliexpress_login_scraper import AliExpressLoginScraper

user_bp = Blueprint('aliexpress/product/info', __name__, url_prefix='/api/aliexpress/product/info')

scraper = AliExpressLoginScraper()


@user_bp.route('/', methods=['GET'])
def get_product_info():
    cookies = AliexpressProductInfoService.get_all_cookie()
    cookie_dicts = [cookie.to_dict() for cookie in cookies]  # 将每个 Cookie 实体转换为字典
    result = {
        'message': '调用成功',
        'cookies': cookie_dicts
    }
    return jsonify(result)
