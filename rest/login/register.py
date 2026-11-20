from flask import render_template, request

from database.connection import PostgresConnectionProvider
from domain.entities.user import StudentRegistration
from usecase.register_student import register_student


def register_route():
    if request.method == "GET":
        return render_template("login/register.html", form={}, errors=[])

    form = request.form
    registration = StudentRegistration(
        first_name=form.get("first_name", "").strip(),
        last_name=form.get("last_name", "").strip(),
        email=form.get("email", "").strip().lower(),
        student_number=form.get("student_number", "").strip(),
        course_title=form.get("course_title", "").strip(),
        password=form.get("password", ""),
    )

    errors = register_student(PostgresConnectionProvider(), registration)
    if errors:
        # Never echo the password back into the form.
        form_values = {key: value for key, value in form.items() if key != "password"}
        return render_template(
            "login/register.html", form=form_values, email=form_values.get("email"), errors=errors
        ), 400

    return render_template("login/register.html", form={}, errors=[], pending_approval=True)
