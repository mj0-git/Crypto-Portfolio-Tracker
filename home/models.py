from django.db import models
from django.db.models.base import Model
from django.db.models.expressions import F
from django.utils import timezone

# Create your models here.
class Portfolio(models.Model):
    
    PORTFOLIO_TYPE_CHOICES = (
        ('investment', 'Investment'),
        ('saving', 'Saving'),
    )

    name = models.CharField(max_length=20)
    cash = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=PORTFOLIO_TYPE_CHOICES, default='investment')
    


    def __str__(self) -> str:
        return self.name

class Asset(models.Model):

    ASSET_TYPE_CHOICES = (
        ('crypto', 'Crypto'),
        ('equity', 'Equity'),
        ('option', 'Option')
    )

    name = models.CharField(max_length=20)
    purchase_date = models.DateField(default=timezone.now)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    target_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stop_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    type = models.CharField(max_length=10, choices=ASSET_TYPE_CHOICES, default='equity')

    OPTION_TYPE_CHOICES = (
        ('calls', 'Call'),
        ('puts', 'Put')
    )
    option_strike = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0.00)
    option_expiry = models.DateField(default=timezone.now, blank=True)
    option_type = models.CharField(max_length=10, choices=OPTION_TYPE_CHOICES, default='calls')

    portfolio = models.ForeignKey('Portfolio', on_delete=models.CASCADE, null=False, default=1)

    def __str__(self) -> str:
        return self.name
     