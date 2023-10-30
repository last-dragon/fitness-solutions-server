from typing import Any

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic import EmailStr

from .config import settings

env = Environment(
    loader=PackageLoader("fitness_solutions_server", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fm = FastMail(conf)


async def send_mail(
    subject, recipients: list[EmailStr], template, template_data: dict[str, Any]
):
    # Generate the HTML template base on the template name
    template = env.get_template(f"emails/{template}.html")

    html = template.render(template_data)

    # Define the message options
    message = MessageSchema(
        subject=subject, recipients=recipients, body=html, subtype="html"
    )

    # Send the email
    await fm.send_message(message)


async def send_user_verification_email(email: str, url: str):
    await send_mail(
        subject="Verify your email address",
        recipients=[EmailStr(email)],
        template="user_verification",
        template_data={"url": url},
    )


async def send_reset_password_email(email: str, url: str):
    await send_mail(
        subject="Reset your Password",
        recipients=[EmailStr(email)],
        template="reset_password",
        template_data={"url": url},
    )
