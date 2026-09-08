from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import NumberRange

class AnimalupdateForm(FlaskForm):
    animal_dog_count=IntegerField(
        "보호 중인 강아지 마리수",
        validators=[NumberRange(min=0, message="0 이상의 숫자를 입력하여 주십시오.")],
        default=0
    )
    animal_cat_count=IntegerField(
        "보호 중인 고양이 마리수",
        validators=[NumberRange(min=0, message="0 이상의 숫자를 입력하여 주십시오.")],
        default=0
    )
    submit=SubmitField("업데이트")