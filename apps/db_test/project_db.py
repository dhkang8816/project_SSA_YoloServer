from datetime import datetime

from apps.app import login_manager
from apps.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, index=True)
    password_hash = db.Column(db.String)
    role = db.Column(db.String, default='user', server_default='user')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_approved = db.Column(db.Boolean, default=False)
    
    @property
    def password(self):
        raise AttributeError("읽어 들일 수 없음")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_duplicate_email(self):
        return User.query.filter_by(email=self.email).first() is not None
    
    def is_admin(self):
        return self.role == 'admin'

    # 드론 요원 확인
    def is_drone(self):
        return self.role == 'drone'

    # 모니터링 요원 확인
    def is_monitoring(self):
        return self.role == 'monitoring'

    # 상황대기조 확인
    def is_standby(self):
        return self.role == 'standby'
    
    @classmethod
    def get_standby_emails(cls):
        """상황대기조의 이메일 목록을 리스트로 반환합니다."""
        results = cls.query.filter_by(role='standby').with_entities(cls.email).all()
        return [email for (email,) in results]
    
    # 승인대기 확인
    def is_pending(self):
        return self.role == 'pending'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)


class Animals(db.Model):
    __tablename__="animals"

    animal_id=db.Column(db.Integer, primary_key=True)
    animal_type=db.Column(db.String, index=True)
    animal_count=db.Column(db.Integer, index=True)

class Detect_animal(db.Model):
    __tablename__="detect_animal"

    detect_id=db.Column(db.Integer, primary_key=True)
    detect_type_count=db.Column(db.String, index=True)
    detect_animal_count=db.Column(db.Integer, index=True)
    detect_day=db.Column(db.DateTime, default=datetime.now)
    detect_alarm=db.Column(db.Boolean, default=False)

class Dangers(db.Model):
    __tablename__="dangers"

    danger_id=db.Column(db.Integer, primary_key=True)
    danger_spec=db.Column(db.String, index=True)
    danger_detect=db.Column(db.DateTime, default=datetime.now)
