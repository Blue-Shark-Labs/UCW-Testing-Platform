from flask import render_template

from rest.helpers.rest_helpers import login_required


@login_required(role="admin")
def admin_dashboard_route():
    return render_template("dashboard/admin.html")
