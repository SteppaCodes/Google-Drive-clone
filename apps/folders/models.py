from django.db import models

from apps.common.models import BaseModel
from apps.accounts.models import User

class Folder(BaseModel):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)


    def __str__(self):
        return self.name