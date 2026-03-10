from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    TelegramAuthView,
    TelegramVerifyView,
    LogoutView,
    MeView,
    UpgradeToSellerView,
    SellerDetailView,
)

urlpatterns = [
    path('get-tg/', TelegramAuthView.as_view(), name='get-tg'),
    path('verify-tg/', TelegramVerifyView.as_view(), name='verify-tg'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/me/', MeView.as_view(), name='me'),
    path('users/me/upgrade-to-seller/', UpgradeToSellerView.as_view(), name='upgrade-to-seller'),
    path('sellers/<int:seller_id>/', SellerDetailView.as_view(), name='seller-detail'),
]