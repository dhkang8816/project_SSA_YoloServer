from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required

from apps.extensions import db
from apps.db_test.project_db import Animals, Dangers, Detect_animal
from apps.detect_data.forms import AnimalupdateForm

from apps.decorator import role_required

from datetime import datetime

dd=Blueprint(
    "detect_data",
    __name__,
    template_folder="templates",
    static_folder="static"
)

@dd.route("/")
def index():
    animal_logs=Animals.query.order_by(Animals.animal_id.desc()).all()
    return render_template("detect_data/index.html")

@dd.route("/animal")
@login_required
@role_required(['admin', 'monitoring'])
def animal_db():
    """유기동물 정보를 취득한다"""
    animals=Animals.query.order_by(Animals.animal_id.desc()).all()
    form = AnimalupdateForm()
    return render_template("detect_data/index.html", animals=animals, form=form)

@dd.route("/animal/update", methods=["GET", "POST"])
@login_required
@role_required(['admin', 'monitoring'])
def update_animals():
    forms = AnimalupdateForm()
    if request.method == "POST":
        try:
            type_set = request.form.get("animal_type", "dog")
            count_set = int(request.form.get("animal_count", 0))

            # 💡 [변경 핵심] DB에 해당 동물 종류(dog/cat)가 이미 있는지 먼저 조회합니다.
            existing_animal = Animals.query.filter_by(animal_type=type_set).first()

            if existing_animal:
                # 1. 이미 존재한다면 기존 데이터의 마리수만 '덮어씌우기(Update)'
                existing_animal.animal_count = count_set
                flash(f"{'강아지' if type_set == 'dog' else '고양이'}의 기준 개체수가 {count_set}마리로 수정되었습니다.")
            else:
                # 2. 만약 DB 초기 상태라 해당 동물이 없다면 '새로 등록(Insert)'
                new_log = Animals(animal_type=type_set, animal_count=count_set)
                db.session.add(new_log)
                flash(f"{'강아지' if type_set == 'dog' else '고양이'}의 기준 개체수가 새로 등록되었습니다.")

            db.session.commit()
            return redirect(url_for("detect_data.animal_db"))
        
        except Exception as e:
            db.session.rollback()
            flash(f"등록 실패: {e}")

    # GET 요청 시 화면에 보여줄 기존 데이터 조회
    config = Animals.query.order_by(Animals.animal_id.desc()).first()
    return render_template("detect_data/animal_manage.html", config=config)

@dd.route("/danger")
@login_required
@role_required(['admin', 'monitoring', 'drone', 'standby'])
def danger_db():
    # """이상객체 정보를 취득한다"""
    # dangers=Dangers.query.order_by(Dangers.danger_detect.desc()).all()
    
    keyword=request.args.get('keyword')
    query=Dangers.query

    if keyword:
        date_obj = None
        try:
            if '-' in keyword:
                # 2026-06-11 형식
                date_obj = datetime.strptime(keyword, '%Y-%m-%d')
            elif len(keyword) == 8 and keyword.isdigit():
                # 20260611 형식
                date_obj = datetime.strptime(keyword, '%Y%m%d')
        except ValueError:
            date_obj = None
            
        if date_obj:
            # 날짜를 찾았으면 해당 일자 필터링
            query = query.filter(Dangers.danger_detect >= date_obj,
                                 Dangers.danger_detect < datetime(date_obj.year, date_obj.month, date_obj.day + 1))
            
        else:
            query = query.filter(Dangers.danger_spec.contains(keyword))
            
    dangers = query.order_by(Dangers.danger_detect.desc()).all()
    form=AnimalupdateForm()
    return render_template("detect_data/danger_db.html", dangers=dangers, form=form)

@dd.route("/detect_animal")
@login_required
@role_required(['admin', 'monitoring', 'drone', 'standby'])
def detect_animal():
    keyword=request.args.get('keyword')
    query=Detect_animal.query

    if keyword:
        date_obj = None
        try:
            if '-' in keyword:
                # 2026-06-11 형식
                date_obj = datetime.strptime(keyword, '%Y-%m-%d')
            elif len(keyword) == 8 and keyword.isdigit():
                # 20260611 형식
                date_obj = datetime.strptime(keyword, '%Y%m%d')
        except ValueError:
            date_obj = None
            
        if date_obj:
            # 날짜를 찾았으면 해당 일자 필터링
            query = query.filter(Detect_animal.detect_day >= date_obj,
                                 Detect_animal.detect_day < datetime(date_obj.year, date_obj.month, date_obj.day + 1))
            
        else:
            query = query.filter(Detect_animal.detect_type_count.contains(keyword))
            

    detect_animals = query.order_by(Detect_animal.detect_day.desc()).all()
    form=AnimalupdateForm()
    return render_template("detect_data/detect_animal.html", detect_animals=detect_animals, form=form)

@dd.route("/animal/delete/<int:animal_id>", methods=["POST"])
@login_required
@role_required(['admin', 'monitoring'])
def delete_animal(animal_id):
    """선택한 유기동물 데이터를 삭제한다"""
    # 1. 넘겨받은 id로 삭제할 데이터를 조회
    animal = Animals.query.filter_by(animal_id=animal_id).first()
    
    # 2. 안전장치: 데이터가 존재하는 경우에만 삭제 진행
    if animal:
        try:
            db.session.delete(animal)
            db.session.commit()
            flash(f"#{animal_id} 항목이 성공적으로 삭제되었습니다.")
        except Exception as e:
            db.session.rollback()
            flash(f"삭제 중 오류가 발생했습니다: {e}")
    else:
        flash("이미 삭제되었거나 존재하지 않는 항목입니다.")
        
    # 3. 삭제 후 다시 유기동물 목록 페이지로 리다이렉트
    return redirect(url_for("detect_data.animal_db"))

@dd.route("/delete_all_detect", methods=["POST"])
@login_required
@role_required(['admin', 'monitoring', 'drone', 'standby'])
def delete_all_detect_animals():
    """모든 영상 감지 내역 데이터를 일괄 삭제한다"""
    try:
        # Detect_animal 테이블의 모든 레코드 삭제
        db.session.query(Detect_animal).delete()
        db.session.commit()
        flash("모든 영상 감지 기록이 성공적으로 초기화되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"전체 삭제 중 오류가 발생했습니다: {e}", "danger")
        
    return redirect(url_for("detect_data.detect_animal"))

@dd.route("/delete_all_anomaly", methods=["POST"])
@login_required
@role_required(['admin', 'monitoring', 'drone', 'standby'])
def delete_all_anomaly():
    """모든 영상 감지 내역 데이터를 일괄 삭제한다"""
    try:
        db.session.query(Dangers).delete()
        db.session.commit()
        flash("모든 영상 감지 기록이 성공적으로 초기화되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"전체 삭제 중 오류가 발생했습니다: {e}", "danger")
        
    return redirect(url_for("detect_data.danger_db"))

import pandas as pd
import io
from flask import send_file

@dd.route("/download/<string:table_name>")
@login_required
@role_required(['admin', 'monitoring', 'drone', 'standby'])
def download_excel(table_name):
    # 1. 테이블 이름에 따라 적절한 모델과 데이터 선택
    if table_name == "detect_animal":
        data_list = Detect_animal.query.all()
        columns = {"ID": "detect_id", "감지된 동물": "detect_type_count", "감지된 마리수": "detect_animal_count", "감지 일시": "detect_day", "알람 발송 여부": "detect_alarm"}
    elif table_name == "dangers":
        data_list = Dangers.query.all()
        columns = {"ID": "danger_id", "감지된 이상객체 종류": "danger_spec", "감지 일시": "danger_detect"}
    else:
        return "잘못된 경로입니다.", 404

    # 2. 데이터 변환 (위의 columns 매핑 정보를 활용)
    data = [{name: getattr(log, field) for name, field in columns.items()} for log in data_list]
    
    # 3. Pandas로 엑셀 생성 (위에서 쓴 로직과 동일)
    df = pd.DataFrame(data)
    
    # 4. Pandas를 이용해 엑셀 파일 생성
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='DetectionLogs')
    output.seek(0)
    
    # 5. 파일 반환
    return send_file(
        output,
        download_name=f"{table_name}_data.xlsx",  # 테이블 이름에 따라 파일명이 바뀝니다
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

