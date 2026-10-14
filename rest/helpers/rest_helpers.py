# Shared helpers for REST route handlers.

from flask import jsonify, request


def wants_json():
    """Returns True if the client requested a JSON response via query parameter."""
    return request.args.get("json") in ("1", "true", "True")


def json_response(message, status_code=200):
    """Returns a JSON response with the given message and status code."""
    if isinstance(message, dict):
        return jsonify(message), status_code
    return jsonify({"message": message}), status_code
