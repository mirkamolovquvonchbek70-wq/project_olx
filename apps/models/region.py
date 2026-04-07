from django.db import models
from django.db.models import CharField, ForeignKey
from django.utils.text import slugify

from apps.models.base import SlugBaseModel


class Region(SlugBaseModel):
    name = CharField(max_length=150, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class City(SlugBaseModel):
    region = ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='cities'
    )
    name = CharField(max_length=150)

    class Meta:
        unique_together = ('region', 'name')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.region.name})'