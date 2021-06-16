from django.db import models


class Prometheus(models.Model):
    jobname = models.CharField("jobname", max_length=255)
    porta = models.IntegerField("porta")

    def __str__(self):
        return self.jobname
