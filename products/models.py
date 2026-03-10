from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    icon = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order_num = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)  # ← null=True qo'shildi

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = (
        ('moderatsiyada', 'Moderatsiyada'),
        ('aktiv', 'Aktiv'),
        ('rad etilgan', 'Rad etilgan'),
        ('sotilgan', 'Sotilgan'),
        ('arxivlangan', 'Arxivlangan'),
    )
    CONDITION_CHOICES = (
        ('yangi', 'Yangi'),
        ('ideal', 'Ideal'),
        ('yaxshi', 'Yaxshi'),
        ('qoniqarli', 'Qoniqarli'),
    )
    PRICE_TYPE_CHOICES = (
        ('qatiy', "Qat'iy"),
        ('kelishiladi', 'Kelishiladi'),
        ('bepul', 'Bepul'),
        ('ayirboshlash', 'Ayirboshlash'),
    )

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='yangi')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES, default='qatiy')
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    view_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='moderatsiyada')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} - rasm {self.order}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} → {self.product.title}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('kutilyapti', 'Kutilyapti'),
        ('kelishilgan', 'Kelishilgan'),
        ('sotib olingan', 'Sotib olingan'),
        ('bekor qilingan', 'Bekor qilingan'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales')
    final_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='kutilyapti')
    meeting_location = models.CharField(max_length=255, blank=True)
    meeting_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.buyer.username} → {self.product.title}"


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_reviews')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.username} → {self.seller.username} ({self.rating})"