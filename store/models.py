from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/', blank=True, help_text='Image shown on storefront banner')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class HomepageImage(models.Model):
    """Images for the storefront homepage banner/gallery"""
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='homepage/')
    link_url = models.CharField(max_length=500, blank=True, help_text='URL to link to when clicked (e.g. /category/1/)')
    order = models.IntegerField(default=0, help_text='Lower = shows first')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f'Homepage Image #{self.id}'

    class Meta:
        ordering = ['order', '-created_at']


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.IntegerField(help_text='Price in sen. RM 10.00 = 1000')  # in sen
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def price_display(self):
        """Convert sen to RM for display"""
        return f"RM {self.price / 100:.2f}"

    def first_image(self):
        """Get the first image for list view"""
        images = self.images.all()
        if images:
            return images[0].image.url
        return None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.name}"


class Order(models.Model):
    """Tracks a full order with shipping details and payment status"""
    COURIER_CHOICES = [
        ('none', 'Not Assigned'),
        ('poslaju', 'Pos Laju'),
        ('jnt', 'J&T Express'),
        ('dhl', 'DHL'),
        ('fedex', 'FedEx'),
        ('citylink', 'City-Link Express'),
        ('gdex', 'GDEX'),
        ('lalamove', 'Lalamove'),
    ]

    order_id = models.CharField(max_length=20, unique=True, blank=True)  # ORD-001
    email = models.EmailField()
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    courier = models.CharField(max_length=20, choices=COURIER_CHOICES, default='none')
    tracking_number = models.CharField(max_length=100, blank=True)
    stripe_session_id = models.CharField(max_length=200, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id} - {self.name} - {'PAID' if self.paid else 'PENDING'}"

    def total_price(self):
        """Sum of all order items"""
        total = 0
        for item in self.items.all():
            total += item.price_at_purchase * item.quantity
        return total

    def total_display(self):
        return f"RM {self.total_price() / 100:.2f}"


class OrderItem(models.Model):
    """Individual product line within an order"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_purchase = models.IntegerField()  # snapshot of price in sen

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def line_total_display(self):
        return f"RM {(self.price_at_purchase * self.quantity) / 100:.2f}"
