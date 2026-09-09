import logging  # 🛠️ 로그 필터링을 위해 logging 라이브러리 추가
from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask import session, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from apps.config import config
from apps.extensions import db

# =================================================================
# 🛠️ [관제 허브 로그 폭발 완치] 3초마다 들어오는 labels_feed 로그만 콘솔에서 숨기기
# =================================================================
class NoLabelsFilter(logging.Filter):
    def filter(self, record):
        # 웹 서버 엔진 로그 메시지 중 'labels_feed'가 들어가 있으면 화면 출력을 차단합니다.
        return "labels_feed" not in record.getMessage()

# Flask가 사용하는 기본 웹 로거(werkzeug)를 강제로 가져와 필터 적용
flask_log = logging.getLogger('werkzeug')
flask_log.addFilter(NoLabelsFilter())
# =================================================================

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "employee.signup"
login_manager.login_message = ""

def create_app(config_key):
    app = Flask(__name__)
    app.config.from_object(config[config_key])
    
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    
    from apps.db_test import project_db
    login_manager.init_app(app)
    
    # crud 패키지로부터 views를 import한다
    from apps.crud import views as crud_views
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
        
        # 2. 권한 정책 정의
        ACCESS_POLICIES = {
            'crud': ['admin'],
            'control_page': ['admin', 'drone', 'monitoring', 'standby'],
            'stream': ['admin', 'monitoring']
        }
        
        # 3. 권한 체크 로직
        current_role = session.get('role')
        allowed_roles = ACCESS_POLICIES.get(request.blueprint)
        
        if allowed_roles and current_role not in allowed_roles:
            flash("접근 권한이 없습니다.")
            return redirect(request.referrer or url_for('main.index'))
            
    return app
