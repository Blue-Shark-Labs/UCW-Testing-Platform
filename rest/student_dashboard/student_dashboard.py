import csv
from collections import defaultdict
from datetime import datetime
from io import StringIO

from flask import abort, g, make_response, render_template, url_for

from database.helpers.database_helpers import get_assigned_tests, get_completed_tests

_CHART_WIDTH = 720
_CHART_HEIGHT = 240
_CHART_LEFT = 42
_CHART_RIGHT = 12
_CHART_TOP = 12
_CHART_BOTTOM = 30


def student_dashboard_route():
    student_id = _student_id()
    assigned_tests = get_assigned_tests(student_id) if student_id else []
    completed_tests = get_completed_tests(student_id) if student_id else []
    return render_template(
        "student_dashboard/page.html",
        assigned_tests=assigned_tests,
        completed_tests=completed_tests,
    )


def student_statistics_route():
    student_id = _student_id()
    completed_tests = get_completed_tests(student_id) if student_id else []
    summary = _summarize_statistics(completed_tests)
    chart_points = _build_chart_points(completed_tests)
    return render_template(
        "student_dashboard/statistics.html",
        summary=summary,
        chart_points=chart_points,
        chart_path=" ".join(
            f"{point['x']},{point['y']}" for point in chart_points
        ),
        export_url=url_for("statistics.student_statistics_export_route"),
    )


def student_statistics_export_route():
    student_id = _student_id()
    completed_tests = get_completed_tests(student_id) if student_id else []
    summary = _summarize_statistics(completed_tests)

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        (
            "Test",
            "Subject",
            "Completed At",
            "Questions",
            "Score (%)",
            "Points",
            "Test Average Score (%)",
            "Highlight",
        )
    )
    for test in completed_tests:
        test_average = summary["test_averages"].get(
            _test_key(test), {}
        ).get("average")
        highlight = _test_highlight(test_average, summary)
        completed_at = test.get("completed_at")
        writer.writerow(
            (
                test.get("test_name", ""),
                test.get("subject_name", ""),
                completed_at.strftime("%Y-%m-%d") if completed_at else "",
                test.get("question_count", ""),
                _format_csv_score(test.get("percentage")),
                test.get("total_points")
                if test.get("total_points") is not None
                else "",
                _format_csv_score(test_average),
                highlight,
            )
        )

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        'attachment; filename="student-statistics.csv"'
    )
    return response


def _summarize_statistics(completed_tests):
    scored_tests = [test for test in completed_tests if test.get("percentage") is not None]
    score_total = sum(float(test["percentage"]) for test in scored_tests)
    test_scores = defaultdict(list)
    for test in completed_tests:
        if test.get("percentage") is not None:
            test_scores[_test_key(test)].append(float(test["percentage"]))

    test_averages = {
        key: {
            "average": sum(scores) / len(scores),
            "test_name": next(
                test.get("test_name", "")
                for test in completed_tests
                if _test_key(test) == key
            ),
        }
        for key, scores in test_scores.items()
    }
    averages = [item["average"] for item in test_averages.values()]
    best_average = max(averages) if averages else None
    worst_average = min(averages) if averages else None
    return {
        "total_points": sum(
            int(test["total_points"])
            for test in completed_tests
            if test.get("total_points") is not None
        ),
        "average_score": score_total / len(scored_tests) if scored_tests else None,
        "completed_count": len(completed_tests),
        "test_averages": test_averages,
        "best_average": best_average,
        "worst_average": worst_average,
        "best_test_names": [
            item["test_name"]
            for item in test_averages.values()
            if item["average"] == best_average
        ],
        "worst_test_names": [
            item["test_name"]
            for item in test_averages.values()
            if item["average"] == worst_average
        ],
        "best_tests": sum(
            item["average"] == max(averages) for item in test_averages.values()
        ) if averages else 0,
        "worst_tests": sum(
            item["average"] == min(averages) for item in test_averages.values()
        ) if averages else 0,
    }


def _test_key(test):
    return test.get("test_id") or test.get("test_name", "")


def _test_highlight(test_average, summary):
    if test_average is None:
        return ""
    is_best = test_average == summary["best_average"]
    is_worst = test_average == summary["worst_average"]
    if is_best and is_worst:
        return "Best and worst"
    if is_best:
        return "Best"
    if is_worst:
        return "Worst"
    return ""


def _format_csv_score(score):
    return f"{float(score):.1f}" if score is not None else ""


def _build_chart_points(completed_tests):
    scored_tests = sorted(
        (
            test
            for test in completed_tests
            if test.get("percentage") is not None
            and test.get("completed_at") is not None
        ),
        key=lambda test: test["completed_at"],
    )
    if not scored_tests:
        return []

    plot_width = _CHART_WIDTH - _CHART_LEFT - _CHART_RIGHT
    plot_height = _CHART_HEIGHT - _CHART_TOP - _CHART_BOTTOM
    last_index = len(scored_tests) - 1
    points = []
    for index, test in enumerate(scored_tests):
        x = (
            _CHART_LEFT + plot_width * index / last_index
            if last_index
            else _CHART_LEFT + plot_width / 2
        )
        score = max(0, min(100, float(test["percentage"])))
        y = _CHART_TOP + plot_height * (100 - score) / 100
        completed_at = test["completed_at"]
        points.append(
            {
                "x": round(x, 1),
                "y": round(y, 1),
                "date": (
                    completed_at.strftime("%d %b")
                    if isinstance(completed_at, datetime)
                    else str(completed_at)
                ),
                "score": float(test["percentage"]),
                "test_name": test.get("test_name", ""),
            }
        )
    return points


def _student_id():
    user = getattr(g, "user", None)
    if str(getattr(user, "role", "student")).lower() != "student":
        abort(403)
    return getattr(user, "user_id", None)