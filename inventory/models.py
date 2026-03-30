from django.db import models

class Inventory(models.Model):
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, related_name='inventory')
    product = models.ForeignKey('core.Product', on_delete=models.CASCADE, related_name='inventory')
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('branch', 'product')
        verbose_name_plural = "Inventories"

    def __str__(self):
        return f"{self.product.name} at {self.branch.name} - {self.stock_quantity}"
