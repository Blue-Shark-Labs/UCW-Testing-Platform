from rest.router import create_app

app = create_app()


@app.get("/health")
def health():
    # Do not return secrets, environment variables, or dependency details here.
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # Development only. Production uses Gunicorn from the Dockerfile.
    app.run(debug=True)
