from django.db import models

from apps.common.models import BaseModel
from apps.accounts.models import User

class File(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='flles')

    def __str__(self):
        return self.file.name
