from flask import render_template

from database.connection import PostgresConnectionProvider
from usecase.get_landing_page_content import get_landing_page_content


def home_route():
    content = get_landing_page_content(PostgresConnectionProvider())
    return render_template("home.html", content=content)
