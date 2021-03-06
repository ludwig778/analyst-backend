from datetime import datetime

import pandas as pd

from django.db import models

from adapters import redis


class UpdateMixin:
    def update_values(self, **new_values):
        updated = False

        for k, v in new_values.items():
            if getattr(self, k) != v:
                setattr(self, k, v)
                updated = True

        if updated:
            self.save()

        return updated


class Asset(models.Model, UpdateMixin):

    class Meta:
        ordering = ['id']

    ASSET_TYPE = (
        ('I', 'Indice'),
        ('S', 'Stock'),
        ('F', 'Forex'),
        ('C', 'Crypto-currency')
    )
    ASSET_TYPE_DICT = dict(ASSET_TYPE)

    name = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=1, choices=ASSET_TYPE, null=True)
    ticker = models.CharField(max_length=30, null=True)

    country = models.CharField(max_length=64, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    init_source = models.CharField(max_length=32)
    data_source = models.CharField(max_length=32)

    extra_data = models.JSONField(null=True, default=dict)

    @property
    def timeserie_label(self):
        return f"asset_{self.id}"

    @property
    def dataframe(self):
        if data := redis.get(self.timeserie_label):
            return pd.read_json(data).sort_index()

    def store_dataframe(self, dataframe):
        redis.set(self.timeserie_label, dataframe.to_json())

        self.updated_at = datetime.now()
        self.save()

    def __str__(self):
        return f"<Asset {self.name}>"

    def up_to_date(self):
        return datetime.now().date() == self.updated_at.date()


class Index(models.Model, UpdateMixin):

    class Meta:
        ordering = ['id']
        verbose_name_plural = "Indexes"

    name = models.CharField(max_length=30, unique=True)
    asset = models.OneToOneField(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="indice",
        null=True
    )

    components = models.ManyToManyField(Asset)
    country = models.CharField(max_length=64, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    init_source = models.CharField(max_length=32)

    def __str__(self):
        return f"<Index {self.name}>"


class Portfolio(models.Model):

    class Meta:
        ordering = ['id']

    name = models.CharField(max_length=30, unique=True)
    assets = models.ManyToManyField(Asset)
    indices = models.JSONField(null=True, default=dict)
    weights = models.JSONField(null=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<Portfolio {self.name}>"
