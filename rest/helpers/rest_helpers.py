# Shared helpers for REST route handlers.

from functools import wraps

from flask import jsonify, make_response, redirect, request, session, url_for


def wants_json():
    """Returns True if the client requested a JSON response via query parameter."""
    return request.args.get("json") in ("1", "true", "True")


def json_response(message, status_code=200):
    """Returns a JSON response with the given message and status code."""
    if isinstance(message, dict):
        return jsonify(message), status_code
    return jsonify({"message": message}), status_code


def login_required(role=None):
    """Redirects to the login page unless there's an authenticated session (optionally for a specific role)."""

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session or (role is not None and session.get("role") != role):
                return redirect(url_for("login_route"))
            # Stop the browser from re-showing protected pages from cache after logout.
            response = make_response(view(*args, **kwargs))
            response.headers["Cache-Control"] = "no-store"
            return response

        return wrapped_view

    return decorator
