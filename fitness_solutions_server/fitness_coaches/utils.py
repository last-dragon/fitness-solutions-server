from pydantic import EmailStr

from fitness_solutions_server.core.config import settings
from fitness_solutions_server.core.email import send_mail


async def send_fitness_coach_activation_email(email: str, token: str):
    url = f"{settings.BASE_URL}/v1/fitness-coaches/auth/activate/{token}"
    await send_mail(
        subject="Activate your account",
        recipients=[EmailStr(email)],
        template="fitness_coach_activation",
        template_data={"url": url},
    )
