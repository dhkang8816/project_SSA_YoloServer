from flask_wtf.form import FlaskForm
from wtforms.fields.simple import SubmitField

class UsercontrolForm(FlaskForm):
    submit=SubmitField("사용자 관리")

class ControlForm(FlaskForm):
    submit=SubmitField("관제")