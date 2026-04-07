from django.db.models import CASCADE, JSONField, IntegerField
from django.db.models.fields import CharField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from apps.models.base import SlugBaseModel, ImageBaseModel


class Category(SlugBaseModel, ImageBaseModel, MPTTModel):
    name = CharField(max_length=255)
    parent = TreeForeignKey('self', CASCADE, null=True, blank=True, related_name='children')
    attribute = JSONField(blank=True, null=True)
    count_products = IntegerField(default=0)



    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']
