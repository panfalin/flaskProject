from app.aliexpress.models.cookie import Cookie


class AliexpressProductInfoService:
    @staticmethod
    def get_all_cookie():
        return Cookie.query.all()
