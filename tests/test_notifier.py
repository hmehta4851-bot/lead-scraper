import os
import unittest
from unittest.mock import MagicMock, patch

import notifier


class NotifierTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "GMAIL_USER": "robot@example.com",
                "GMAIL_APP_PASSWORD": "app-password",
                "NOTIFY_EMAIL": "management@example.com",
            },
            clear=False,
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    @patch("notifier.time.sleep", return_value=None)
    @patch("notifier.smtplib.SMTP_SSL")
    def test_notification_retries_then_succeeds(self, smtp_ssl, _sleep):
        connection = MagicMock()
        smtp_ssl.side_effect = [OSError("temporary outage"), connection]
        connection.__enter__.return_value = connection

        notifier.send_notification(
            "Status",
            "Body",
            attempts=3,
            retry_delay=0,
        )

        self.assertEqual(smtp_ssl.call_count, 2)
        connection.login.assert_called_once()
        connection.sendmail.assert_called_once()

    @patch("notifier.time.sleep", return_value=None)
    @patch(
        "notifier.smtplib.SMTP_SSL",
        side_effect=OSError("persistent outage"),
    )
    def test_notification_raises_after_retry_exhaustion(
        self,
        smtp_ssl,
        _sleep,
    ):
        with self.assertRaisesRegex(
            RuntimeError,
            "failed after 3 attempts",
        ):
            notifier.send_notification(
                "Status",
                "Body",
                attempts=3,
                retry_delay=0,
            )

        self.assertEqual(smtp_ssl.call_count, 3)

    @patch.dict(
        os.environ,
        {"GMAIL_USER": "", "GMAIL_APP_PASSWORD": ""},
        clear=False,
    )
    def test_notification_fails_closed_without_credentials(self):
        with self.assertRaisesRegex(RuntimeError, "Email notification required"):
            notifier.send_notification("Status", "Body")

    @patch("notifier.send_notification")
    def test_existing_completion_sends_management_confirmation(self, send):
        notifier.notify_existing_completion(
            "Mumbai, Maharashtra",
            {"Playful": 35, "Powerful": 52},
            50,
            35,
        )

        subject = send.call_args.kwargs["subject"]
        body = send.call_args.kwargs["body"]
        self.assertIn("COMPLETION CONFIRMED", subject)
        self.assertIn("Playful", body)
        self.assertIn("35/50", body)
        self.assertIn("Daily enough floor: 35", body)
        self.assertIn("No duplicate collection", body)


if __name__ == "__main__":
    unittest.main()
