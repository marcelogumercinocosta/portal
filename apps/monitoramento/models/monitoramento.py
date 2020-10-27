# -*- coding: utf-8 -*-

from django.db import models


class TipoMonitoramento(models.Model):
    nome = models.CharField("nome", max_length=255)

    class Meta:
        verbose_name = "Tipo"
        verbose_name_plural = "Tipos"
        ordering = ("nome",)

    def __str__(self):
        return self.nome


class Monitoramento(models.Model):
    TARGETS = (
        ("_blank", "nova aba"),
        (" ", "sem target"),
    )

    nome = models.CharField("nome", max_length=255)
    url = models.URLField("url")
    prioridade = models.IntegerField("prioridade")
    target = models.CharField("target", max_length=10, choices=TARGETS)
    tipo = models.ForeignKey(TipoMonitoramento, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Monitoramento"
        verbose_name_plural = "Monitoramentos"
        ordering = ("tipo", "prioridade", "nome")

    def __str__(self):
        return self.nome
