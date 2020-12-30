from django.db import models

class Measurement(models.Model):
    date = models.IntegerField(unique=True)
    sisalla = models.FloatField(null=True)
    ulkona = models.FloatField(null=True)
    jarvessa = models.FloatField(null=True)
    rauhalassa = models.FloatField(null=True)
    kellarissa = models.FloatField(null=True)
    saunassa = models.FloatField(null=True)

