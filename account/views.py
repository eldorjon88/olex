from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from redis import Redis
from uuid import uuid4
import json
from .servise import create_user, get_tokens_for_user
from .models import CustomUser
from django.conf import settings


class TelegramAuth(APIView):

    def get(self, request: Request) -> Response:
        redis = Redis(host='localhost', port=6379, db=0)
        unicID = str(uuid4())
        redis.set(unicID, 'empty', ex=900)
        tg_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={unicID}"  # ← to'g'rilandi
        redis.close()
        return Response({"tg_url": tg_url, "unicID": unicID}, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        redis = Redis(host='localhost', port=6379, db=0)
        data = request.data
        unicID = data.get("unicID")

        if not unicID:
            return Response({"error": "unicID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if redis.exists(unicID):
            redis_value = redis.get(unicID)
            if not redis_value:
                redis.close()
                return Response({"error": "invalid unicID or time end"}, status=status.HTTP_400_BAD_REQUEST)

            redis_value = redis_value.decode() if isinstance(redis_value, bytes) else redis_value

            if redis_value == 'empty':
                redis.close()
                return Response({"error": "Telegram verification pending"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                tokens = json.loads(redis_value)
            except Exception as e:
                redis.close()
                return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)

            redis.close()
            return Response({"tokens": tokens}, status=status.HTTP_200_OK)
        else:
            redis.close()
            return Response({"error": "invalid unicID or time end"}, status=status.HTTP_400_BAD_REQUEST)


class TelegramVerificationView(APIView):

    def post(self, request: Request) -> Response:
        data = request.data
        unicID = data.get("unicID")

        if not unicID:
            return Response({"error": "unicID is required"}, status=status.HTTP_400_BAD_REQUEST)

        redis = Redis(host='localhost', port=6379, db=0)

        if not redis.exists(unicID):
            redis.close()
            return Response(
                {"status": "error", "message": "Invalid or expired unicID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        redis_data = redis.get(unicID)

        if not redis_data:
            redis.close()
            return Response({"error": "invalid"}, status=status.HTTP_400_BAD_REQUEST)

        data = json.loads(redis_data.decode())
        redis.delete(unicID)

        user = CustomUser.objects.filter(telegram_id=data['telegram_id']).first()

        if not user:
            user = create_user(data=data)

        tokens = json.dumps(get_tokens_for_user(user=user))
        redis.set(unicID, tokens, ex=900)
        redis.close()

        return Response({"status": "successful"}, status=status.HTTP_201_CREATED)


class UserLoginAPIView(APIView):

    def post(self, request: Request) -> Response:
        telegram_id = request.data.get("telegram_id")

        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.filter(telegram_id=telegram_id).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        tokens = get_tokens_for_user(user=user)
        return Response({"tokens": tokens}, status=status.HTTP_200_OK)