from functools import wraps
from flask import session, redirect, url_for, flash, request

ROLE_NAMES = {
    'admin': '관리자',
    'drone': '드론 요원',
    'monitoring': '모니터링',
    'standby': '상황대기조'
}

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. role이 리스트라면 [role]로 감싸서 리스트 통일
            allowed_roles = role if isinstance(role, list) else [role]
            
            # 2. 현재 유저의 역할이 허용된 리스트에 포함되어 있는지 확인
            if session.get('role') not in allowed_roles:
                # 3. 필요한 역할들의 한글 이름을 리스트로 추출
                role_labels = [ROLE_NAMES.get(r, r) for r in allowed_roles]
                role_label_str = ", ".join(role_labels)
                
                flash(f"접근 권한이 없습니다.")
                return redirect(request.referrer or url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator