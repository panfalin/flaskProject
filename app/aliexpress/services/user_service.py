from app.aliexpress.models.user import User
from app.core.services.db import db


class UserService:
    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def get_user_by_id(user_id):
        success, results = db.query()\
            .select('*')\
            .from_table('users')\
            .where(id=user_id)\
            .execute()
        return results[0] if results else None

    @staticmethod
    def create_user(data):
        with db.transaction() as cursor:
            success = db.create('users', data)
            return success

    @staticmethod
    def update_user(user_id, data):
        user = User.query.get_or_404(user_id)
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
