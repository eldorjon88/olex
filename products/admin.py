from django.contrib import admin
from .models import Category, Product, ProductImage, Favorite, Order, Review

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Favorite)
admin.site.register(Order)
admin.site.register(Review)