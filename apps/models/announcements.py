from django.conf import settings
from django.db.models import CharField, CASCADE, ForeignKey, JSONField, TextChoices, Model, DateTimeField, SET_NULL
from django.db.models.constraints import UniqueConstraint
from django.db.models.fields import PositiveIntegerField, PositiveSmallIntegerField, TextField


from apps.models.base import ImageBaseModel, SlugBaseModel, CreatedBaseModel




class Announcement(SlugBaseModel, CreatedBaseModel):
    class AnnouncementType(TextChoices):
        SIMPLE = "simple", "SIMPLE"
        VIP = "vip", "VIP"

    class SellerTypeChoices(TextChoices):
        PRIVATE = "private", "PRIVATE"
        BUSINESS = "business", "BUSINESS"

    name = CharField(max_length=255)
    price = PositiveIntegerField()
    description = TextField(blank=True)
    category = ForeignKey('apps.Category', CASCADE, related_name='announcements')
    product_type = CharField(max_length=10, choices=AnnouncementType.choices, default=AnnouncementType.SIMPLE)
    attribute = JSONField(blank=True, null=True)
    seller_type = CharField(max_length=10,choices=SellerTypeChoices.choices, default=SellerTypeChoices.PRIVATE)
    user = ForeignKey("apps.User", CASCADE, related_name='announcements')
    city = ForeignKey("apps.City", on_delete=CASCADE, related_name='announcements')


    @property
    def first_image(self):
        img = self.images.first()
        return img.image.url if img else "/static/img/no-photo.png"


class AnnouncementImage(ImageBaseModel):
    product = ForeignKey('apps.Announcement', CASCADE, related_name='images')


class Favorite(Model):
    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="favorites"
    )
    announcement = ForeignKey(
        "Announcement",
        on_delete=CASCADE,
        related_name="favorited_by"
    )
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "announcement"],
                name="unique_user_announcement_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.announcement}"
