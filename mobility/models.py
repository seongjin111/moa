# from django.db import models

# Create your models here.
from django.db import models

class BusStop(models.Model):
    name = models.CharField(max_length=120)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    has_shelter = models.BooleanField(default=True)
    has_braille_block = models.BooleanField(default=True)

    def __str__(self):
        return self.name
