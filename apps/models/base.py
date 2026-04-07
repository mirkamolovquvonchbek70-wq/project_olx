from django.core.validators import FileExtensionValidator
from django.db.models import Model, SlugField, ImageField, DateTimeField
from django.utils.text import slugify
from apps.models.utils import upload_to_image, upload_image_size_5mb_validator


class SlugBaseModel(Model):
    slug = SlugField(max_length=255, unique=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding:
            if hasattr(self, 'name'):
                self.slug = slugify(self.name)

            if hasattr(self, 'title'):
                self.slug = slugify(self.title)
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class ImageBaseModel(Model):
    image = ImageField(upload_to=upload_to_image, null=True, blank=True,
                       validators=[FileExtensionValidator(['jpeg', 'jpg', 'png', 'webp']),
                                   upload_image_size_5mb_validator],
                       help_text='jpg, png, webp are allowed')

    class Meta:
        abstract = True


class CreatedBaseModel(Model):
    updated_at = DateTimeField(auto_now_add=True)
    created_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True
