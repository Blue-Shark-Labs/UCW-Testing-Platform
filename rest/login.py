from flask import render_template


def login_route():
    return render_template("login.html")
