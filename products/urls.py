from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductImageViewSet,
    FavoriteViewSet,
    OrderViewSet,
    ReviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'favorites', FavoriteViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]