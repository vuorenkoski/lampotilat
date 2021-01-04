from django.db import models

class Temperature(models.Model):
    date = models.IntegerField(unique=True)
    Sisalla = models.FloatField(null=True)
    Ulkona = models.FloatField(null=True)
    Jarvessa = models.FloatField(null=True)
    Rauhalassa = models.FloatField(null=True)
    Kellarissa = models.FloatField(null=True)
    Saunassa = models.FloatField(null=True)
    Roykassa = models.FloatField(null=True)
    Tuuli = models.FloatField(null=True)
    Tuulimax = models.FloatField(null=True)
    Sade = models.FloatField(null=True)
    Liike = models.FloatField(null=True)
    Lumi = models.FloatField(null=True)


