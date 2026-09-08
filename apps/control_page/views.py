from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

from apps.control_page.forms import LivestreamForm, VideostreamForm, AnimaldbForm, DangerdbForm, AnimaldetectdbForm

control_page=Blueprint(
    "control_page",
    __name__,
    template_folder="templates"
)

@control_page.route("/")
@login_required
def index():
    return render_template("control_page/index.html")

@control_page.route("/livestream")
@login_required
def livestream():
    form=LivestreamForm()
    return render_template("control_page/livestream.html")

@control_page.route("/animaldb")
@login_required
def animaldb():
    form=AnimaldbForm()
    return redirect(url_for('detect.animal'))

@control_page.route("/dangerdb")
@login_required
def dangerdb():
    form=DangerdbForm()
    return redirect(url_for('detect.danger'))

@control_page.route("/detectanimaldb")
@login_required
def detectanimaldb():
    form=AnimaldetectdbForm
    return redirect(url_for('detect.detect_animal'))