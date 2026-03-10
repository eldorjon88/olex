from rest_framework import serializers
from .models import CustomUser, SellerProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'telegram_id', 'username', 'first_name', 'last_name',
                  'phone_number', 'role', 'avatar']
        read_only_fields = ['id', 'telegram_id', 'role']


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = '__all__'
        read_only_fields = ['user', 'rating', 'total_sales']


class UpgradeToSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'shop_description', 'shop_logo', 'region', 'district', 'address']


class TelegramLoginSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, default='')
    photo_url = serializers.CharField(required=False, allow_null=True)