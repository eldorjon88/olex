from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from redis import Redis
from uuid import uuid4
from django.conf import settings
import json

from .models import CustomUser, SellerProfile
from .serializers import UserSerializer, SellerProfileSerializer, UpgradeToSellerSerializer
from .service import get_tokens_for_user, create_user


class TelegramAuthView(APIView):
    """GET: Telegram URL olish | POST: Token olish"""

    def get(self, request):
        redis = Redis(host='localhost', port=6379, db=0)
        unicID = str(uuid4())
        redis.set(unicID, 'empty', ex=900)
        redis.close()
        tg_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={unicID}"
        return Response({"tg_url": tg_url, "unicID": unicID})

    def post(self, request):
        unicID = request.data.get("unicID")
        if not unicID:
            return Response({"error": "unicID is required"}, status=400)

        redis = Redis(host='localhost', port=6379, db=0)

        if not redis.exists(unicID):
            redis.close()
            return Response({"error": "Invalid or expired unicID"}, status=400)

        redis_value = redis.get(unicID).decode()

        if redis_value == 'empty':
            redis.close()
            return Response({"error": "Telegram verification pending"}, status=400)

        try:
            tokens = json.loads(redis_value)
        except Exception as e:
            redis.close()
            return Response({"error": str(e)}, status=400)

        redis.close()
        return Response({"tokens": tokens})


class TelegramVerifyView(APIView):
    """Bot dan kelgan ma'lumotlarni saqlash"""

    def post(self, request):
        unicID = request.data.get("unicID")
        if not unicID:
            return Response({"error": "unicID is required"}, status=400)

        redis = Redis(host='localhost', port=6379, db=0)

        if not redis.exists(unicID):
            redis.close()
            return Response({"error": "Invalid or expired unicID"}, status=400)

        redis_data = redis.get(unicID)
        if not redis_data:
            redis.close()
            return Response({"error": "Invalid"}, status=400)

        data = json.loads(redis_data.decode())
        redis.delete(unicID)

        user = CustomUser.objects.filter(telegram_id=data['telegram_id']).first()
        if not user:
            user = create_user(data=data)

        tokens = get_tokens_for_user(user)
        redis.set(unicID, json.dumps(tokens), ex=900)
        redis.close()

        return Response({"status": "successful"}, status=201)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Muvaffaqiyatli chiqildi"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UpgradeToSellerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'seller_profile'):
            return Response({"error": "Siz allaqachon sotuvchisiz"}, status=400)

        serializer = UpgradeToSellerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            request.user.role = 'seller'
            request.user.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class SellerDetailView(APIView):
    def get(self, request, seller_id):
        try:
            profile = SellerProfile.objects.get(id=seller_id)
            serializer = SellerProfileSerializer(profile)
            return Response(serializer.data)
        except SellerProfile.DoesNotExist:
            return Response({"error": "Topilmadi"}, status=404)