from django.contrib.auth.models import AbstractUser
from django.db.models.fields import EmailField, CharField, IntegerField
from apps.models.managers import CustomUserManager
from apps.models.utils import uz_phone_validator


class User(AbstractUser):
    email = EmailField("email address", unique=True)
    phone = CharField(max_length=15, validators=[uz_phone_validator], null=True, blank=True, unique=True)
    username = None
    objects = CustomUserManager()
    balance = IntegerField(default=0)
    bonus = IntegerField(default=0)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    @property
    def is_valid_password(self):
        return self.has_usable_password()
