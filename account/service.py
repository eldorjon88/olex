from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def create_user(data: dict) -> CustomUser:
    user = CustomUser.objects.create(
        telegram_id=data['telegram_id'],
        username=data.get('username', f"user_{data['telegram_id']}"),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
    )
    return user
