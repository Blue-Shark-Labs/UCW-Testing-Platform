from flask import render_template

from rest.helpers.rest_helpers import login_required


@login_required()
def pr_block_route():
    return render_template("pr_block/page.html")
