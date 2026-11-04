from flask import render_template

from database.connection import PostgresConnectionProvider
from usecase.get_landing_page_content import get_landing_page_content

# Page-authored marketing content: not modeled in the database, so it's hardcoded here.
CAROUSEL_SLIDES = [
    {
        "title": "Multiple-Choice Testing",
        "description": "Lecturers create multiple-choice tests for students to complete online.",
    },
    {
        "title": "Track Your Progress",
        "description": "Students monitor their average percentage, points, and progress over time.",
    },
    {
        "title": "Compete On The Leaderboard",
        "description": "See how you rank against classmates on each subject's top five leaderboard.",
    },
    {
        "title": "Built For Every Role",
        "description": "Secure single sign-on for students, lecturers, and senior management alike.",
    },
]

GALLERY_IMAGES = [
    {
        "src": "images/admin-view.png",
        "alt": "Lecturer portal for managing students, tests, and approvals",
    },
    {
        "src": "images/student-view.png",
        "alt": "Student multiple-choice test view with live scoring",
    },
    {
        "src": "images/student-leaderboard.png",
        "alt": "Subject leaderboard ranking the top five students",
    },
]


def landing_page_route():
    connection_provider = PostgresConnectionProvider()
    company_info = get_landing_page_content(connection_provider)
    return render_template(
        "landing_page/landing-page.html",
        company_info=company_info,
        carousel_slides=CAROUSEL_SLIDES,
        gallery_images=GALLERY_IMAGES,
    )
