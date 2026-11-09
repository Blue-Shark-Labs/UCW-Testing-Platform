# House Style Guide — Student Quiz Web Application

**Version:** 1.1  
**Purpose:** To establish consistent design, coding and collaboration standards for the student quiz web application.

## 1. Introduction

This document defines the standards that all developers should follow when designing, developing and maintaining the student quiz web application.

The application uses Python for back-end functionality and HTML, CSS and Tailwind CSS for the front-end. This guide ensures consistency across the application's visual design, code structure, naming conventions, accessibility and development workflow.

All contributors should follow these standards when creating features, fixing bugs or updating existing functionality.

## 2. Technology Stack

The application uses the following technologies:

| Technology | Purpose |
|---|---|
| Python | Back-end logic, data processing, quiz scoring and server-side functionality |
| HTML | Page structure and semantic content |
| CSS | Custom styling and additional visual presentation |
| Tailwind CSS | Utility-based styling and consistent UI design |
| Git and GitHub | Version control, collaboration and code review |
| Markdown | Project documentation |

The project should use existing frameworks, dependencies and conventions where possible. New libraries should only be introduced when they provide a clear benefit.

## 3. Typography

### Primary font: Roboto

**Roboto** will be the primary font throughout the application. It provides a modern, readable appearance suitable for an educational platform.

| Element | Font size | Font weight |
|---|---|---|
| Main page heading | 32px | 700 |
| Section heading | 24px | 700 |
| Subheading | 20px | 500 |
| Body text | 16px | 400 |
| Supporting text | 14px | 400 |
| Buttons and labels | 16px | 500 |

### Font Implementation

Roboto is loaded in the base.html file and applied sitewide using the Tailwind configuration file:

```
Tailwind config
theme: {
extend: {
colors: {
app: {
background: "#F3F8FC",
divider: "#D9E4EF",
primary: "#1769E0",
secondary: "#6495ED",
ternary: "#89CFF0",
quaternary: "#6082B6",
quinary: "#B6D0E2",
},
text: {
primary: "#13213A",
},
},
fontFamily: {
roboto: ["Roboto", "sans-serif"],
},
},
```

Use font weights consistently: regular for body text, medium for labels and bold for headings.

## 4. Colour Palette

The application will use a blue-based colour palette to create a consistent, professional and approachable educational environment.

| Colour | Hex code | Intended use |
|---|---|---|
| Royal Blue | `#1769E0` | Primary buttons, main actions and prominent headings |
| Cornflower Blue | `#6495ED` | Secondary buttons, links and interactive elements |
| Light Sky Blue | `#89CFF0` | Highlights and selected elements |
| Steel Blue | `#6082B6` | Supporting UI elements, borders and secondary components |
| Powder Blue | `#B6D0E2` | Card backgrounds, panels and section separation |
| White | `#FFFFFF` | Page backgrounds, cards and suitable text backgrounds |
| Dark Grey | `#1F2937` | Main body text on light backgrounds |

### Colour implementation

Palette is defined in the base.html, same as the font, in the Tailwind Config File 

### Colour guidelines

- Use Royal Blue for primary actions such as starting or submitting a quiz.
- Use Cornflower Blue for secondary actions and links.
- Use Light Sky Blue for highlights rather than large amounts of text.
- Use Powder Blue for subtle cards and content panels.
- Use Dark Grey for body text on light backgrounds.
- Do not rely on colour alone to communicate correct answers, incorrect answers or errors.

Ensure that text and interactive components have sufficient contrast and aim to meet WCAG 2.2 AA accessibility requirements.

## 5. Naming Conventions

Consistent naming makes the code easier to understand, review and maintain.

### 5.1 Python naming conventions

Python code should follow the standard Python naming conventions, generally aligned with PEP 8.

| Element | Convention | Example |
|---|---|---|
| Variables | snake_case | `student_name` |
| Functions | snake_case | `calculate_quiz_score()` |
| Classes | PascalCase | `QuizQuestion` |
| Constants | UPPER_SNAKE_CASE | `MAX_QUIZ_ATTEMPTS` |
| Modules | lowercase, preferably snake_case | `quiz_helpers.py` |
| Private implementation details | Leading underscore where appropriate | `_validate_answer()` |

Although camelCase is used for front-end variables, **Python variables and functions should use snake_case** to follow established Python conventions.

Example:

```python
MAX_QUIZ_ATTEMPTS = 3


def calculate_quiz_score(correct_answers, total_questions):
    if total_questions == 0:
        return 0

    return (correct_answers / total_questions) * 100


def has_submitted_quiz(student_id):
    # Check whether the student has submitted the quiz.
    return False
```

Use descriptive names that explain what a variable or function represents. Avoid unclear abbreviations.

### 5.2 HTML naming conventions

Use lowercase HTML element names and semantic elements wherever possible.

```html
<main>
    <section class="quiz-card">
        <h1>General Knowledge Quiz</h1>
        <p>Answer each question to test your knowledge.</p>

        <button type="button" class="quiz-button">
            Start Quiz
        </button>
    </section>
</main>
```

Use meaningful IDs and class names when needed. IDs should be unique within a page.

### 5.3 CSS naming conventions

Use **kebab-case** for CSS class names and custom properties.

```css
.quiz-card {
    border-radius: 8px;
    padding: 24px;
}

.quiz-question {
    font-size: 20px;
    font-weight: 500;
}

.quiz-button {
    background-color: var(--color-primary);
    color: #FFFFFF;
}
```

Avoid inconsistent naming, such as mixing `quizCard`, `quiz-card` and `quiz_card` for equivalent CSS classes.

### 5.4 Tailwind CSS conventions

Tailwind CSS utility classes should be used for common styling tasks, including layout, spacing, typography, colours and responsive behaviour.

```html
<section class="rounded-lg bg-white p-6 shadow-sm">
    <h1 class="text-2xl font-bold text-gray-900">
        General Knowledge Quiz
    </h1>

    <p class="mt-2 text-base text-gray-700">
        Test your knowledge with this quiz.
    </p>

    <button
        type="button"
        class="mt-4 rounded-md bg-blue-800 px-4 py-2
               font-medium text-white hover:bg-blue-900
               focus-visible:outline-2 focus-visible:outline-offset-2
               focus-visible:outline-blue-800"
    >
        Start Quiz
    </button>
</section>
```

The example illustrates the approach; the final classes should use the application's configured colour palette.

Guidelines:

- Follow a consistent ordering of utility classes.
- Use responsive utilities such as `sm:`, `md:` and `lg:` where appropriate.
- Avoid duplicating long sets of utility classes across multiple components or templates.
- Use reusable HTML templates or project-approved component patterns for repeated UI elements.
- Use custom CSS for styling that is difficult to express clearly with Tailwind utilities.
- Do not introduce unnecessary inline styles.

### 5.5 Naming summary

| Context | Naming convention |
|---|---|
| Python variables | `snake_case` |
| Python functions | `snake_case` |
| Python classes | `PascalCase` |
| Python constants | `UPPER_SNAKE_CASE` |
| HTML elements | Lowercase |
| HTML IDs | `camelCase` or existing project convention, used consistently |
| CSS classes | `kebab-case` |
| CSS variables | `--kebab-case` |
| Tailwind utilities | Standard Tailwind utility syntax |
| File names for Python modules | `snake_case.py` |
| HTML templates | `kebab-case.html` |
| CSS files | `kebab-case.css` |

## 6. Python Back-End Standards

Python is responsible for server-side functionality, including quiz logic, score calculations, data validation and communication with any database or other services.

All Python code should be readable, modular and maintainable.

### Coding guidelines

- Follow PEP 8 for formatting and naming.
- Use four spaces for indentation.
- Keep functions focused on one main responsibility.
- Use descriptive names for variables, functions and classes.
- Avoid unnecessary code duplication.
- Use comments and docstrings to explain complex behaviour and public functions.
- Handle expected errors explicitly.
- Validate incoming data before processing it.
- Keep secrets and credentials out of source control.
- Separate business logic from route or request-handling code where practical.
- Use type hints where they improve clarity and maintainability.

### Example

```python
def calculate_quiz_score(correct_answers: int, total_questions: int) -> float:
    """Return the percentage score for a completed quiz."""
    if total_questions <= 0:
        return 0.0

    return round((correct_answers / total_questions) * 100, 2)
```

Quiz scoring should be consistent and tested against expected results. If the server is responsible for scoring, it should calculate or verify the result rather than trusting a score supplied by the browser.

## 7. HTML, CSS and Tailwind CSS Standards

### HTML

- Use semantic HTML elements such as `header`, `nav`, `main`, `section` and `footer`.
- Use headings in a logical hierarchy.
- Associate form inputs with meaningful labels.
- Use the correct button type, such as `submit` or `button`.
- Keep document structure clear and avoid unnecessary nesting.
- Ensure all interactive elements have accessible names.

### CSS

- Use the central design tokens for colours and shared styling.
- Prefer reusable rules over duplicated declarations.
- Avoid overly specific selectors that are difficult to override.
- Keep responsive behaviour consistent.
- Use custom CSS when Tailwind utilities alone would make the markup unnecessarily complicated.
- Avoid repeating hard-coded colour values when a design token already exists.

### Tailwind CSS

- Use utilities for common layout and styling requirements.
- Use the project's configured design tokens instead of arbitrary colours wherever possible.
- Keep class lists readable and consistent.
- Avoid constructing utility class names dynamically in ways the Tailwind build process cannot detect.
- Use responsive variants to support different screen sizes.
- Use focus and disabled-state utilities for interactive elements.
- Keep the project's Tailwind version and configuration consistent across the team.

## 8. User Interface and Quiz Design

The application should be easy to navigate and allow students to focus on learning.

### General layout

- Use consistent border radii, spacing and alignment.
- Ensure pages work on mobile, tablet and desktop.
- Avoid overcrowding pages with unnecessary information.
- Use clear headings and descriptive button labels.

### Quiz-specific standards

- Display questions and answer options clearly.
- Show progress, for example, "Question 3 of 10".
- Provide clear feedback after an answer is submitted.
- Preserve selected answers when navigating between questions, where appropriate.
- Show the final score and relevant feedback when the quiz is completed.
- Provide clear options to retry a quiz or return to the dashboard.
- Prevent accidental repeated submissions.
- Use consistent layouts for all question types.

## 9. Accessibility

Accessibility should be considered throughout the development process.

- Aim to meet WCAG 2.2 AA standards.
- Ensure the application can be navigated using a keyboard.
- Provide visible focus indicators.
- Use semantic HTML and correctly labelled form controls.
- Maintain sufficient colour contrast.
- Do not rely on colour alone to communicate correct or incorrect answers.
- Provide clear validation messages and error feedback.
- Ensure content remains usable when text is enlarged.
- Use accessible status messages for quiz feedback where appropriate.
- Test interfaces with keyboard navigation and screen readers.

## 10. File and Folder Organisation

Files should be grouped by their responsibilities. The following is a suggested structure that can be adapted to the existing framework and repository.

```text
project/
├── app.py
├── requirements.txt
├── README.md
├── docs/
│   └── house-style.md
├── routes/
│   └── quiz_routes.py
├── services/
│   └── quiz_service.py
├── utils/
│   └── quiz_helpers.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── quiz.html
│   └── results.html
├── static/
│   ├── css/
│   │   └── custom.css
│   ├── js/
│   │   └── quiz.js
│   └── images/
└── tests/
    ├── test_quiz_service.py
    └── test_quiz_routes.py
```

This structure is illustrative rather than mandatory. It should be adjusted to the project's existing architecture, framework and Tailwind build setup. For example, some frameworks organise routes, templates and static assets differently.

## 11. Git and GitHub Workflow

Git and GitHub should be used for version control, collaboration and code review.

### Branch naming convention

Use the following format:

```text
<developer>/<category>/<short-description>
```

Example:

```text
john/design/create-design-document
```

Use lowercase descriptive words for the branch description, separated by hyphens.

### Pull request naming convention

Pull requests must follow the agreed format:

```text
[FEATURE] [FR-05] Allow students to see completed tests
```

### Pull request description template

```markdown
## Summary
Briefly explain the purpose of the changes.

## Related task
FR-05

## Changes made
- Describe the main changes.
- Identify relevant back-end or front-end updates.
- Mention documentation changes where applicable.

## Testing
- List tests performed.
- Include the results of relevant automated checks.

## Screenshots
Add screenshots for relevant UI changes.

## Reviewer notes
Include any important context for reviewers.
```

### Review and merging rules

- Create a separate branch for each feature, bug fix or documentation task.
- Keep pull requests focused on a single main task.
- Test changes before requesting a review.
- Address review feedback before merging.
- Avoid committing secrets, credentials or unnecessary files.
- Write meaningful commit messages.
- Merge only after the required reviews and checks have passed.

## 12. Testing Standards

Testing should verify that features work as expected and that changes do not break existing functionality.

### Back-end testing

Use Python's `unittest` or the project's existing testing framework, such as `pytest`.

Test:

- Quiz score calculations.
- Correct and incorrect answers.
- Empty or invalid submissions.
- Missing or malformed request data.
- Quiz completion and submission behaviour.
- Relevant route responses and error handling.
- Access controls for student records and quiz results.

### Front-end testing

Check:

- Page layouts and styling across supported screen sizes.
- Quiz navigation and answer selection.
- Form validation and error messages.
- Buttons, links and interactive states.
- Keyboard accessibility and focus indicators.
- Browser compatibility.
- Correct use of the configured colour palette and typography.

Run the project's established tests and linting tools before merging changes.

## 13. Security and Student Data

Student data and quiz results must be handled responsibly.

- Validate user input on the server.
- Use appropriate authentication and authorisation.
- Keep private credentials outside source control.
- Use secure session and cookie settings appropriate to the framework.
- Protect against common web vulnerabilities, including cross-site scripting and cross-site request forgery where applicable.
- Use parameterised database queries or a suitable ORM.
- Restrict student records and results to authorised users.
- Collect only the personal information necessary for the application.
- Calculate or verify quiz scores on the server when appropriate.
- Follow applicable data protection requirements.

## 14. Documentation Standards

Project documentation should use Markdown and clear, professional language.

- Use descriptive headings.
- Use fenced code blocks for examples.
- Use tables for structured information.
- Keep documentation updated when functionality or conventions change.
- Document project setup, dependencies and testing instructions.
- Record significant technical decisions when they affect future development.

## 15. Definition of Done

A task is considered complete when:

- [ ] It meets the requirements of the associated feature request.
- [ ] Python code follows the agreed naming and formatting conventions.
- [ ] HTML, CSS and Tailwind CSS follow the house style.
- [ ] The application uses the approved typography and colour palette.
- [ ] Relevant tests have passed.
- [ ] Accessibility has been considered and appropriate checks completed.
- [ ] No secrets or unnecessary debugging code have been committed.
- [ ] Relevant documentation has been updated.
- [ ] The pull request follows the agreed naming convention.
- [ ] Required reviews and approvals have been completed.

## 16. Maintaining the House Style

This document is the shared reference for the development team.

Any new conventions should be agreed upon and documented before being adopted across the project. Existing code should be updated consistently, avoiding unnecessary refactoring that does not contribute to the task.

The overall aim is to maintain an accessible, reliable and visually consistent student quiz application, with Python code that is easy to maintain and a front-end that provides a clear and engaging learning experience.
