from django.db import models
from django.db.models.base import Model
from django.db.models.expressions import F

# Create your models here.

class Asset(models.Model):

    TYPE_CHOICES = (
        ('crypto', 'Crypto'),
        ('equity', 'Equity')
    )

    name = models.CharField(max_length=20)
    purchase_date = models.DateField(auto_now_add=True)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    stop_price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='crypto')


    #type  = models.ForeignKey('Type', on_delete=models.CASCADE, null=False)

    def __str__(self) -> str:
        return self.name
     