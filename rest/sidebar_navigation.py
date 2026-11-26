from copy import deepcopy


_NAVIGATION_BY_ROLE = {
    "student": [
        {"label": "Tests", "icon": "menu", "endpoint": "student_dashboard.student_dashboard_route"},
        {"label": "Subject Leaderboards", "icon": "award", "endpoint": "leaderboards.subject_leaderboards_route"},
        {"label": "Statistics", "icon": "chart", "endpoint": "statistics.student_statistics_route"},
    ],
    "lecturer": [
        {"label": "Home", "icon": "home", "endpoint": "lecturer_dashboard_route"},
        {
            "label": "Management",
            "icon": "sliders",
            "children": [
                {
                    "label": "Student Roster",
                    "icon": "users",
                    "endpoint": "lecturer.lecturer_management_route",
                },
                {
                    "label": "Quiz Management",
                    "icon": "file",
                    "endpoint": "lecturer.quiz_management_route",
                },
            ],
        },
        {
            "label": "Courses/Subjects",
            "endpoint": "lecturer.lecturer_view_subjects_route",
            "icon": "book",
        },
        {"label": "Student Progress", "icon": "chart", "endpoint": "lecturer.student_progress_route"},
        {"label": "Security", "icon": "lock", "endpoint": "account.security_settings_route"},
        {"label": "Help Centre", "icon": "help", "endpoint": "help_centre_route"},
    ],
    "admin": [
        {"label": "Subjects", "icon": "book", "endpoint": "administrator.administrator_view_subjects_route"},
        {"label": "User Management", "icon": "users", "endpoint": "administrator.administrator_view_users_route"},
        {"label": "System Settings", "icon": "sliders", "endpoint": "system_settings_route"},
        {"label": "Security", "icon": "lock", "endpoint": "account.security_settings_route"},
        {"label": "Help Centre", "icon": "help", "endpoint": "help_centre_route"},
    ],
}


def get_sidebar_navigation(role):
    normalized_role = str(role).lower()
    return deepcopy(_NAVIGATION_BY_ROLE.get(normalized_role, _NAVIGATION_BY_ROLE["student"]))