from flask_wtf.form import FlaskForm
from wtforms.fields.simple import SubmitField

class LivestreamForm(FlaskForm):
    submit=SubmitField("실시간 관제")

class VideostreamForm(FlaskForm):
    submit=SubmitField("영상 관제")

class AnimaldbForm(FlaskForm):
    submit=SubmitField("유기동물 관리")

class DangerdbForm(FlaskForm):
    submit=SubmitField("이상객체 관리")

class AnimaldetectdbForm(FlaskForm):
    submit=SubmitField("영상 감지 현황")