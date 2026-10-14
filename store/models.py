from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.IntegerField()
    image = models.ImageField(upload_to='products/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__ (self):
        return self.name

    def price_display(self):
        """convert sen to RM for display """
        return f"RM {self.price / 100:.2f}"


