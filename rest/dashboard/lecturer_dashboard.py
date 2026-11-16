from flask import render_template

from rest.helpers.rest_helpers import login_required


@login_required(role="lecturer")
def lecturer_dashboard_route():
    return render_template("dashboard/lecturer.html")
