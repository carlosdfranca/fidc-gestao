from django.contrib.auth.models import AbstractUser
from django.db import models
from stdimage.models import StdImageField

class CustomUser(AbstractUser):
    profile_image = StdImageField(
        upload_to="users/profile/",
        variations={"thumb": (150, 150, True)},
        default="users/profile/default.png",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
