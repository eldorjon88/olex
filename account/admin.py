from django.contrib import admin
from .models import CustomUser
from .models import CustomUser, SellerProfile

admin.site.register(CustomUser)
admin.site.register(SellerProfile)