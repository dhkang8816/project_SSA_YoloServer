from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, make_response
from flask_login import login_required, current_user 
from apps.extensions import db
from apps.db_test.project_db import User
from apps.crud.forms import UserForm

crud = Blueprint(
    "crud",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@crud.route("/")
def index():
    return render_template("crud/index.html")


@crud.route("/users/new", methods=["GET", "POST"])  # 회원등록
@login_required
def create_user():
    form = UserForm()
    if form.validate_on_submit() and request.method == "POST":
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role='user' 
        )
        
        if user.is_duplicate_email():
            flash("지정한 이메일 주소는 이미 등록되어 있습니다.")
            return redirect(url_for("crud.create_user"))
        
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("crud.users"))
    
    return render_template("crud/create.html", form=form)


@crud.route("/users", methods=["GET", "POST"])
@login_required
def users():
    role = request.args.get('role', 'all')
    if role == 'all':
        users = User.query.all()
    else:
        users = User.query.filter_by(role=role).all()
    return render_template("crud/index.html", users=users)

@crud.route("/users/approve/<int:user_id>", methods=["POST"])
@login_required
def approve_user(user_id):
    # 관리자 권한 확인
    if not current_user.is_admin():
        abort(403)
        
    user = User.query.get_or_404(user_id)
    user.is_approved = True  # 승인 처리
    db.session.commit()
    
    flash(f"{user.username}님의 가입을 승인했습니다.")
    return redirect(url_for("crud.users"))

from werkzeug.security import generate_password_hash

@crud.route("/users/<user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not current_user.is_admin():
        abort(403)

    user = User.query.filter_by(id=user_id).first_or_404()
    form = UserForm(obj=user)
    
    if request.method == "POST":
        # 1. 폼 데이터 반영
        user.role = request.form.get("role")
        user.username = request.form.get("username")
        user.email = request.form.get("email")
        
        # 2. 비밀번호 해싱 반영
        if request.form.get("password"):
            user.password = generate_password_hash(request.form.get("password"))
        
        db.session.commit()
        
        # 3. HTMX 요청일 때 새로고침 응답
        if request.headers.get('HX-Request'):
            response = make_response("수정 완료")
            response.headers['HX-Refresh'] = 'true'
            return response
            
        return redirect(url_for("crud.users"))
    
    # ... 아래는 기존과 동일
    if request.headers.get('HX-Request'):
        return render_template("crud/edit_modal.html", user=user, form=form)
    
    return render_template("crud/edit_html.html", user=user, form=form)


@crud.route("/users/delete/<user_id>", methods=["GET"]) # 회원 삭제
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        abort(403)
        
    user = User.query.filter_by(id=user_id).first_or_404()
    
    db.session.delete(user)
    db.session.commit()

    flash(f"{user.username}사용자가 성공적으로 삭제되었습니다.")
    # html 파일 오픈 대신 리다이렉트로 목록 화면 갱신
    return redirect(url_for("crud.users"))
