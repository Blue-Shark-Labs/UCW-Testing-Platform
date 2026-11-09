from copy import deepcopy


_NAVIGATION_BY_ROLE = {
    "student": [
        {"label": "Home", "icon": "home", "endpoint": "pr_block.pr_block_route"},
        {
            "label": "Tests & Quizzes",
            "icon": "menu",
            "children": [
                {"label": "Assigned Tests", "icon": "clock", "endpoint": "assigned_tests_route"},
                {"label": "Completed History", "icon": "check", "endpoint": "completed_history_route"},
                {
                    "label": "Subject Leaderboards",
                    "icon": "award",
                    "endpoint": "subject_leaderboards_route",
                },
            ],
        },
        {"label": "Settings", "icon": "sliders", "endpoint": "settings_route"},
        {"label": "Help Centre", "icon": "help", "endpoint": "help_centre_route"},
    ],
    "lecturer": [
        {"label": "Home", "icon": "home", "endpoint": "lecturer_home_route"},
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
                    "label": "Test Management",
                    "icon": "file",
                    "endpoint": "lecturer_tests.test_management_route",
                },
            ],
        },
        {"label": "Courses/Subjects", "icon": "book", "endpoint": "administrator.administrator_view_subjects_route"},
        {"label": "Student Progress", "icon": "chart", "endpoint": "student_progress_route"},
        {"label": "Help Centre", "icon": "help", "endpoint": "help_centre_route"},
    ],
    "administrator": [
        {"label": "Home", "icon": "home", "endpoint": "admin_home_route"},
        {"label": "User Management", "icon": "users", "endpoint": "user_management_route"},
        {"label": "Courses/Subjects", "icon": "book", "endpoint": "administrator.administrator_view_subjects_route"},
        {"label": "System Settings", "icon": "sliders", "endpoint": "system_settings_route"},
        {"label": "Help Centre", "icon": "help", "endpoint": "help_centre_route"},
    ],
}


def get_sidebar_navigation(role):
    normalized_role = str(role).lower()
    return deepcopy(_NAVIGATION_BY_ROLE.get(normalized_role, _NAVIGATION_BY_ROLE["student"]))