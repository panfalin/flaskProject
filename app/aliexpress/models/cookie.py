from datetime import datetime

from app import db


class Cookie(db.Model):
    __tablename__ = 'sys_cookie'

    s_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键')
    project = db.Column(db.String(255), nullable=True, comment='项目名')
    username = db.Column(db.String(100), nullable=True, comment='账户')
    password = db.Column(db.String(100), nullable=True, comment='密码')
    cooking_context = db.Column(db.Text, nullable=True, comment='cookie内容')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    create_by = db.Column(db.String(255), nullable=True, comment='创建人')
    update_by = db.Column(db.String(255), nullable=True, comment='更新人')
    expired_time = db.Column(db.DateTime, nullable=True, comment='过期时间')

    def to_dict(self):
        return {
            's_id': self.s_id,
            'project': self.project,
            'username': self.username,
            'password': self.password,
            'cooking_context': self.cooking_context,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'expire_time': self.expired_time.isoformat() if self.expired_time else None
        }
