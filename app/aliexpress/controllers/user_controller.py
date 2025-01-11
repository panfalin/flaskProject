from flask import Blueprint, jsonify, request

from app.aliexpress.services.user_service import UserService

user_bp = Blueprint('user', __name__, url_prefix='/api/users')


@user_bp.route('/', methods=['GET'])
def get_users():
    users = UserService.get_all_users()
    return jsonify([user.to_dict() for user in users])


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = UserService.get_user_by_id(user_id)
    return jsonify(user.to_dict())


@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    user = UserService.create_user(data)
    return jsonify(user.to_dict()), 201


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = UserService.update_user(user_id, data)
    return jsonify(user.to_dict())


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    UserService.delete_user(user_id)
    return jsonify({'message': f'用户 {user_id} 删除成功'}), 204
