# Django
from django.conf import settings

# Third Party
import mandrill
import requests

def send_mandrill_email(html, text, subject, email):
    """
    html = html template instance
    text = text template instance
    subject = "The subject of the message"
    email = [{"email": email}]
    """
    mandrill_email = mandrill.Mandrill(settings.MANDRILL_KEY)

    mandrill_data = {
            "html": html,
            "text": text,
            "subject": subject,
            "from_email": settings.ADMIN_EMAIL["from_gopher"],
            "to": email
        }

    return mandrill_email.messages.send(message=mandrill_data)


def send_to_pushover(balance):
    response = requests.post()
