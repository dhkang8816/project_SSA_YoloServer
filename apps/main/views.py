from flask import Blueprint, render_template, redirect, request, Response, url_for

from flask_login import login_required

from apps.main.forms import UsercontrolForm, ControlForm

main=Blueprint(
    "main",
    __name__,
    template_folder="templates"
)

@main.route("/")
def index():
    return render_template("main/index.html")

@main.route("/userctrl")
@login_required
def userctrl():
    form=UsercontrolForm()
    return redirect(url_for('crud.users'))

@main.route("/control")
@login_required
def control():
    form=ControlForm
    return render_template("control_page/index.html", form=form)

