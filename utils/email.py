import threading
from decouple import config
import resend


resend.api_key = config("RESEND_API_KEY")


class EmailThread(threading.Thread):
    """Send Resend emails asynchronously."""

    def __init__(self, to_email, subject, html):
        threading.Thread.__init__(self)
        self.to_email = to_email
        self.subject = subject
        self.html = html

    def run(self):
        try:
            resend.Emails.send({
                "from": "onboarding@resend.dev",  # or your verified domain
                "to": self.to_email,
                "subject": self.subject,
                "html": self.html,
            })
        except Exception as e:
            print("Resend email error:", e)

