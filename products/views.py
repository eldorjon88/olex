from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import timedelta

from .models import Category, Product, ProductImage, Favorite, Order, Review
from .serializers import (
    CategorySerializer, ProductSerializer, ProductImageSerializer,
    FavoriteSerializer, OrderSerializer, ReviewSerializer
)
from .permissions import IsSeller, IsOwner


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True, parent=None)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, slug=None):
        category = self.get_object()
        products = Product.objects.filter(category=category, status='aktiv')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'region', 'condition', 'price_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'view_count']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Product.objects.all()  # ← barcha mahsulotlar
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view_count += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(
            seller=self.request.user,
            expires_at=timezone.now() + timedelta(days=30)
        )

    def perform_update(self, serializer):
        serializer.save(status='moderatsiyada')

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({"error": "Ruxsat yo'q"}, status=403)
        product.status = 'aktiv'
        product.published_at = timezone.now()
        product.save()
        return Response({"status": "E'lon chop etildi"})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({"error": "Ruxsat yo'q"}, status=403)
        product.status = 'arxivlangan'
        product.save()
        return Response({"status": "Arxivlandi"})

    @action(detail=True, methods=['post'])
    def sold(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({"error": "Ruxsat yo'q"}, status=403)
        product.status = 'sotilgan'
        product.save()
        if hasattr(request.user, 'seller_profile'):
            request.user.seller_profile.total_sales += 1
            request.user.seller_profile.save()
        return Response({"status": "Sotilgan deb belgilandi"})


class ProductImageViewSet(viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductImage.objects.filter(product__seller=self.request.user)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        favorite = serializer.save(user=self.request.user)
        favorite.product.favorite_count += 1
        favorite.product.save()

    def perform_destroy(self, instance):
        instance.product.favorite_count -= 1
        instance.product.save()
        instance.delete()


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = self.request.query_params.get('role')
        if role == 'seller':
            return Order.objects.filter(seller=user)
        elif role == 'buyer':
            return Order.objects.filter(buyer=user)
        return Order.objects.filter(buyer=user) | Order.objects.filter(seller=user)

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        serializer.save(
            buyer=self.request.user,
            seller=product.seller,
            final_price=product.price
        )

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.data.get('status')
        user = request.user

        if user == order.seller and new_status in ['kelishilgan', 'bekor qilingan']:
            order.status = new_status
            order.meeting_location = request.data.get('meeting_location', order.meeting_location)
            order.meeting_time = request.data.get('meeting_time', order.meeting_time)
            order.save()
            return Response(OrderSerializer(order).data)

        if user == order.buyer and new_status in ['sotib olingan', 'bekor qilingan']:
            order.status = new_status
            order.save()
            if new_status == 'sotib olingan':
                order.product.status = 'sotilgan'
                order.product.save()
                if hasattr(order.seller, 'seller_profile'):
                    order.seller.seller_profile.total_sales += 1
                    order.seller.seller_profile.save()
            return Response(OrderSerializer(order).data)

        return Response({"error": "Bu amalni bajarishga ruxsat yo'q"}, status=403)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    http_method_names = ['get', 'post']

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Review.objects.all()
        seller_id = self.request.query_params.get('seller_id')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        return queryset

    def perform_create(self, serializer):
        order = serializer.validated_data['order']

        if order.status != 'sotib olingan':
            raise serializers.ValidationError("Faqat sotib olingan buyurtma uchun fikr qoldirish mumkin")

        if order.buyer != self.request.user:
            raise serializers.ValidationError("Faqat xaridor fikr qoldira oladi")

        review = serializer.save(
            reviewer=self.request.user,
            seller=order.seller
        )

        seller = order.seller
        reviews = Review.objects.filter(seller=seller)
        avg = sum(r.rating for r in reviews) / reviews.count()
        if hasattr(seller, 'seller_profile'):
            seller.seller_profile.rating = avg
            seller.seller_profile.save()