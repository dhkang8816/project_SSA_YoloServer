
# 앱 기능을 위해
from apps.extensions import db
from apps.auth.forms import SignUpForm, LoginForm  
from apps.db_test.project_db import User
from flask_login import login_user, logout_user

# 앱 구조를 위해 
from flask import (
    Blueprint, 
    flash, 
    redirect, 
    render_template, 
    request, 
    url_for,
    session
)

# Blueprint를 사용해서 auth를 생성한다
auth = Blueprint("auth", 
                 __name__, 
                 template_folder="templates", 
                 static_folder="static"
                 )

# index 엔드포인트를 작성한다
@auth.route("/")
def index():
    return render_template("auth/index.html")


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    
    #forms.py 적용시
    form = SignUpForm()
    if form.validate_on_submit() and request.method == "POST":
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            is_approved=False
        )

        # 메일 주소 중복 체크를 한다
        if user.is_duplicate_email():
            flash("지정한 이메일 주소는 이미 등록되어 있습니다.")
            return redirect(url_for("auth.signup"))

        # 사용자 정보를 등록한다
        db.session.add(user)
        db.session.commit()

        flash("가입이 완료되었습니다.")
        return redirect(url_for("auth.login"))

    next_ = request.args.get("next")
    if next_ is not None and next_.startswith("/"):
        return redirect(url_for("auth.index"))
    
    return render_template("auth/signup.html",form=form)

@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()    
    
    if form.validate_on_submit() and request.method == 'POST':
        # 메일 주소로부터 사용자를 취득한다
        user = User.query.filter_by(email=form.email.data).first()
        
        # 사용자가 존재하고 비밀번호가 일치하는 경우는 로그인을 허가한다
        if user is not None and user.verify_password(form.password.data):
            
            if not user.is_approved:
                flash("관리자의 승인을 기다리는 중입니다. 잠시만 기다려주세요.")
                return redirect(url_for("auth.login"))

            # [핵심] 로그인 성공 시 역할(role)을 세션에 저장합니다!
            session['role'] = user.role  # DB의 role 값을 세션에 복사
            
            # 사용자 정보를 세션에 저장(Flask-Login)
            login_user(user)
            return redirect(url_for("main.index"))
            
        flash("메일 주소 혹은 패스워드가 일치하지 않습니다.")
        
        
    return render_template("auth/login.html",form=form)
    

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))    