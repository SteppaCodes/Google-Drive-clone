from django.db import models

from apps.common.models import BaseModel
from apps.accounts.models import User
from apps.folders.models import Folder

class File(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='flles')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')

    def __str__(self):
        return self.file.name
