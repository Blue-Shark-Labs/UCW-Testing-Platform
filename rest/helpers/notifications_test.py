# To Run: pytest rest/helpers/notifications_test.py

import smtplib

from rest.helpers.notifications import send_student_approval_email


class TestSendStudentApprovalEmail:
    def test_skips_dispatch_when_smtp_host_not_configured(self, monkeypatch):
        monkeypatch.delenv("SMTP_HOST", raising=False)

        result = send_student_approval_email("sam@dev.local", "Sam")

        assert result is False

    def test_uses_smtp_ssl_for_port_465(self, monkeypatch):
        events = []

        class FakeSMTPSSL:
            def __init__(self, host, port, timeout=10):
                events.append(("init_ssl", host, port, timeout))

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def starttls(self):
                events.append(("starttls",))

            def login(self, user, password):
                events.append(("login", user, password))

            def send_message(self, msg):
                events.append(("send_message", msg["To"], msg["From"]))

        monkeypatch.setenv("SMTP_HOST", "plesk.remote.ac")
        monkeypatch.setenv("SMTP_PORT", "465")
        monkeypatch.setenv("SMTP_USER", "noreply@bluesharklabs.remote.ac")
        monkeypatch.setenv("SMTP_PASSWORD", "secret")
        monkeypatch.setenv("SMTP_FROM", "noreply@bluesharklabs.remote.ac")
        monkeypatch.setenv("SMTP_USE_TLS", "true")
        monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTPSSL)

        result = send_student_approval_email("sam@dev.local", "Sam")

        assert result is True
        assert events == [
            ("init_ssl", "plesk.remote.ac", 465, 10),
            ("login", "noreply@bluesharklabs.remote.ac", "secret"),
            ("send_message", "sam@dev.local", "noreply@bluesharklabs.remote.ac"),
        ]

    def test_uses_smtp_with_starttls_for_port_587(self, monkeypatch):
        events = []

        class FakeSMTP:
            def __init__(self, host, port, timeout=10):
                events.append(("init_smtp", host, port, timeout))

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def starttls(self):
                events.append(("starttls",))

            def login(self, user, password):
                events.append(("login", user, password))

            def send_message(self, msg):
                events.append(("send_message", msg["To"], msg["From"]))

        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "secret")
        monkeypatch.delenv("SMTP_FROM", raising=False)
        monkeypatch.delenv("SMTP_USE_SSL", raising=False)
        monkeypatch.delenv("SMTP_USE_TLS", raising=False)
        monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

        result = send_student_approval_email("sam@dev.local", "Sam")

        assert result is True
        assert events == [
            ("init_smtp", "smtp.example.com", 587, 10),
            ("starttls",),
            ("login", "user@example.com", "secret"),
            ("send_message", "sam@dev.local", "user@example.com"),
        ]