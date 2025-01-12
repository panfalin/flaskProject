from app import db
from app.aliexpress.models.user import User


class UserService:
    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get_or_404(user_id)

    @staticmethod
    def create_user(data):
        user = User(name=data['name'], email=data['email'])
        db.session.add(user)
        db.session.commit()
        return user

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
