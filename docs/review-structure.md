# PR Review Structure

This document describes how pull requests are communicated and reviewed for the UCW Testing Platform.

## Post the PR in Chat

When a PR is ready for review, post a message in the Teams chat linking the PR and a short summary of what changed.

```text
🔔 PR Ready for Review: BSL-01: Add question entity validation
Link: <PR URL>
Summary: Adds question validation rules and tests.
```

## Reviewer Message & Status Icons

After reviewing, the reviewer reacts directly to the chat with one of the statuses below, so the author can tell the outcome at a glance.

### Comments Added

The reviewer has left feedback that needs to be addressed before the PR can be approved. (Add reaction -> Search "message")

![Reviewer added comments](img/comment-teams.png)

### Approved

The reviewer is satisfied with the changes and the PR is ready to merge. If you only see one approval, remember two are needed to merge the PR so please review also. (Add reaction -> Search "check")

![Reviewer approved](img/approve-teams.png)

## Review Approval Checklist (Definintion of Done)

Before approving a PR, confirm the following:

- [ ] Code builds/runs locally with no errors
- [ ] All tests pass (`pytest` / relevant test suite)
- [ ] New code has adequate test coverage
- [ ] No unrelated or debug code left in the diff
- [ ] Naming and structure follow existing project conventions
- [ ] No obvious security issues (input validation, secrets, SQL injection, etc.)
- [ ] Documentation/comments updated if behavior changed
- [ ] PR description clearly explains the change and its purpose

