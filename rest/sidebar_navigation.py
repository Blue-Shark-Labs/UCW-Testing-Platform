from copy import deepcopy


_NAVIGATION_BY_ROLE = {
    "student": [
        {"label": "Tests", "icon": "menu", "endpoint": "student_dashboard.student_dashboard_route"},
        {"label": "Subject Leaderboards", "icon": "award", "endpoint": "leaderboards.subject_leaderboards_route"},
        {"label": "Statistics", "icon": "chart", "endpoint": "statistics.student_statistics_route"},
        {"label": "Home", "icon": "home", "endpoint": "pr_block.pr_block_route"},
        {
            "label": "Tests",
            "icon": "menu",
            "endpoint": "student_dashboard.student_dashboard_route",
            "active_endpoints": ["student_dashboard.take_test"],
        },
        {"label": "Subject Leaderboards", "icon": "award", "endpoint": "leaderboards.subject_leaderboards_route"},
        {
            "label": "Statistics",
            "icon": "chart",
            "endpoint": "statistics.student_statistics_route",
            "active_endpoints": ["statistics.student_statistics_export_route"],
        },
        {"label": "Settings", "icon": "sliders", "endpoint": "settings_route"},
        {"label": "Security", "icon": "lock", "endpoint": "account.security_settings_route"},
        {"label": "Privacy", "icon": "privacy", "endpoint": "privacy_policy_route"},
    ],
    "lecturer": [
        {"label": "Dashboard", "icon": "home", "endpoint": "lecturer.lecturer_dashboard_route"},
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
                    "active_endpoints": ["lecturer.quiz_statistics_route"],
                },
            ],
        },
        {
            "label": "Subjects",
            "endpoint": "lecturer.lecturer_view_subjects_route",
            "icon": "book",
        },
        {
            "label": "Student Progress",
            "icon": "chart",
            "endpoint": "lecturer.student_progress_route",
            "active_endpoints": ["lecturer.student_progress_detail_route"],
        },
        {"label": "Security", "icon": "lock", "endpoint": "account.security_settings_route"},
        {"label": "Privacy", "icon": "privacy", "endpoint": "privacy_policy_route"},
    ],
    "admin": [
        {"label": "Subjects", "icon": "book", "endpoint": "administrator.administrator_view_subjects_route"},
        {"label": "User Management", "icon": "users", "endpoint": "administrator.administrator_view_users_route"},
        {
            "label": "Students & Tests",
            "icon": "sliders",
            "children": [
                {
                    "label": "Student Roster",
                    "icon": "users",
                    "endpoint": "lecturer.lecturer_management_route",
                },
                {
                    "label": "Student Progress",
                    "icon": "chart",
                    "endpoint": "lecturer.student_progress_route",
                    "active_endpoints": ["lecturer.student_progress_detail_route"],
                },
                {
                    "label": "Quiz Management",
                    "icon": "file",
                    "endpoint": "lecturer.quiz_management_route",
                    "active_endpoints": ["lecturer.quiz_statistics_route"],
                },
            ],
        },
        {"label": "Security", "icon": "lock", "endpoint": "account.security_settings_route"},
        {"label": "Privacy", "icon": "privacy", "endpoint": "privacy_policy_route"},
    ],
}


def get_sidebar_navigation(role):
    normalized_role = str(role).lower()
    return deepcopy(_NAVIGATION_BY_ROLE.get(normalized_role, _NAVIGATION_BY_ROLE["student"]))