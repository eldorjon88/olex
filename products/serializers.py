from rest_framework import serializers
from .models import Category, Product, ProductImage, Favorite, Order, Review


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'icon', 'description',
                  'is_active', 'order_num', 'children']

    def get_children(self, obj):
        return CategorySerializer(obj.children.filter(is_active=True), many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'order', 'is_main']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'seller', 'seller_name', 'category', 'title', 'description',
                  'condition', 'price', 'price_type', 'region', 'district',
                  'view_count', 'favorite_count', 'status', 'created_at',
                  'published_at', 'expires_at', 'images']
        read_only_fields = ['seller', 'view_count', 'favorite_count', 'status',
                            'published_at', 'expires_at']


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['user']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'product', 'buyer', 'seller', 'final_price', 'status',
                  'meeting_location', 'meeting_time', 'notes', 'created_at']
        read_only_fields = ['buyer', 'seller', 'final_price', 'status']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'order', 'reviewer', 'seller', 'rating', 'comment', 'created_at']
        read_only_fields = ['reviewer', 'seller']
