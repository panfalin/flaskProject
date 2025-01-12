from app.aliexpress.models.cookie import Cookie
from app.core.services.database_manager import DatabaseManager


class AliexpressProductInfoService:
    @staticmethod
    def get_all_cookie():
        return Cookie.query.all()
