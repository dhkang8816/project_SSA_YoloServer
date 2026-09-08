from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask import session, redirect, url_for, flash, request

from flask_wtf.csrf import CSRFProtect

from apps.config import config
from apps.extensions import db

csrf=CSRFProtect()

login_manager=LoginManager()
login_manager.login_view="employee.signup"
login_manager.login_message=""

def create_app(config_key):
    app=Flask(__name__)
    app.config.from_object(config[config_key])

    csrf.init_app(app)

    db.init_app(app)
    Migrate(app,db)
    from apps.db_test import project_db

    login_manager.init_app(app)

    # crud 패키지로부터 views를 import한다
    from apps.crud import views as crud_views
    # register_blueprint를 사용해 views의 crud를 앱에 등록한다
    app.register_blueprint(crud_views.crud, url_prefix="/crud")
    
    from apps.auth import views as auth_views
    app.register_blueprint(auth_views.auth, url_prefix="/auth")

    from apps.main import views as main_views
    app.register_blueprint(main_views.main)

    from apps.detect_data import views as dd_views
    app.register_blueprint(dd_views.dd, url_prefix="/detect")
    
    from apps.control_page import views as control_views
    app.register_blueprint(control_views.control_page, url_prefix="/control")

    from apps.stream import views as stream_views
    app.register_blueprint(stream_views.stream, url_prefix="/stream")

    from apps.esp32 import views as esp32_views
    app.register_blueprint(esp32_views.esp32_yolov12, url_prefix="/esp32_yolov12")

    @app.before_request
    def check_access_control():
        if request.blueprint in ['auth', 'main', 'esp32_yolov12', 'stream']:
            return
        # 1. 예외 경로 설정
        if 'video_feed' in request.path:
            return

        # 2. 권한 정책 정의 (이 부분만 수정하면 전체 보안 정책이 바뀜)
        # { 블루프린트명: 허용된 역할들 }
        ACCESS_POLICIES = {
            'crud': ['admin'],
            'control_page': ['admin', 'drone', 'monitoring', 'standby'],
            'stream': ['admin', 'monitoring']
        }

        # 3. 권한 체크 로직
        current_role = session.get('role')
        allowed_roles = ACCESS_POLICIES.get(request.blueprint)

        # 정의된 정책에 해당하는데, 권한이 없는 경우
        if allowed_roles and current_role not in allowed_roles:
            flash("접근 권한이 없습니다.")
            return redirect(request.referrer or url_for('main.index'))

    return app
