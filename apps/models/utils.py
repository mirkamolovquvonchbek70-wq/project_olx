from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models.fields.files import ImageFieldFile

uz_phone_validator = RegexValidator(
    regex=r'^(\+998|998)?[0-9]{9}$',
    message="Telefon raqam +998901234567 formatida bo‘lishi kerak"
)


def upload_image_size_5mb_validator(obj: ImageFieldFile):
    if obj.size > 5 * 1024 * 1024:
        raise ValidationError(f'This image is too big (max - 5mb) {obj.size / 1024 / 1024:.2f} MB')
    return obj


def upload_to_image(obj, filename: str):
    _name = obj.__class__.__name__.lower()
    date_path = datetime.now().strftime("%Y/%m/%d")

    return f"{_name}/{date_path}/{filename}"
