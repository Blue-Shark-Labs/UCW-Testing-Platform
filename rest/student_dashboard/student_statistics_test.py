import csv
from datetime import datetime
from io import StringIO
from types import SimpleNamespace

from flask import g

from rest.student_dashboard import student_dashboard as dashboard_module


def _completed_tests():
    return [
        {
            "attempt_id": "attempt-3",
            "test_id": "algebra",
            "test_name": "Algebra Check",
            "subject_name": "Mathematics",
            "completed_at": datetime(2026, 11, 3),
            "question_count": 10,
            "percentage": 90.0,
            "total_points": 100,
        },
        {
            "attempt_id": "attempt-2",
            "test_id": "biology",
            "test_name": "Biology Check",
            "subject_name": "Science",
            "completed_at": datetime(2026, 11, 2),
            "question_count": 8,
            "percentage": 50.0,
            "total_points": 0,
        },
        {
            "attempt_id": "attempt-1",
            "test_id": "algebra",
            "test_name": "Algebra Check",
            "subject_name": "Mathematics",
            "completed_at": datetime(2026, 11, 1),
            "question_count": 10,
            "percentage": 80.0,
            "total_points": 90,
        },
    ]


def test_statistics_page_shows_totals_average_chart_and_highlights(client, monkeypatch):
    monkeypatch.setattr(
        dashboard_module, "get_completed_tests", lambda student_id: _completed_tests()
    )

    response = client.get("/statistics")

    assert response.status_code == 200
    assert b"Total points" in response.data
    assert b"190" in response.data
    assert b"Average score" in response.data
    assert b"73.3%" in response.data
    assert b"Grades over time" in response.data
    assert b"<polyline" in response.data
    assert b"Algebra Check" in response.data
    assert b"Biology Check" in response.data
    assert b'href="/statistics/export.csv"' in response.data


def test_export_csv_marks_best_and_worst_tests_by_average(client, monkeypatch):
    monkeypatch.setattr(
        dashboard_module, "get_completed_tests", lambda student_id: _completed_tests()
    )

    response = client.get("/statistics/export.csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment; filename=\"student-statistics.csv\"" in response.headers["Content-Disposition"]
    rows = list(csv.DictReader(StringIO(response.get_data(as_text=True))))
    assert [row["Highlight"] for row in rows] == ["Best", "Worst", "Best"]
    assert [row["Test Average Score (%)"] for row in rows] == ["85.0", "50.0", "85.0"]


def test_statistics_routes_require_student_role(app, client):
    @app.before_request
    def set_lecturer():
        g.user = SimpleNamespace(role="lecturer", user_id="lecturer-id")

    assert client.get("/statistics").status_code == 403
    assert client.get("/statistics/export.csv").status_code == 403


def test_empty_student_export_still_has_csv_headers(client, monkeypatch):
    monkeypatch.setattr(dashboard_module, "get_completed_tests", lambda student_id: [])

    response = client.get("/statistics/export.csv")

    assert response.status_code == 200
    assert next(csv.reader(StringIO(response.get_data(as_text=True)))) == [
        "Test",
        "Subject",
        "Completed At",
        "Questions",
        "Score (%)",
        "Points",
        "Test Average Score (%)",
        "Highlight",
    ]
