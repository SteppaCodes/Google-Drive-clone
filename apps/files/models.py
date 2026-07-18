from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel  #, StarredItem
from apps.folders.models import Folder


class File(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='files')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_files')

    def __str__(self):
        return self.name


class Comment(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()

    def __str__(self):
        return self.comment[:100]


class FileVersion(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    file_instance = models.FileField(upload_to='file_versions/')
    diff_content = models.TextField(blank=True) # Unified diff representation
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.file.name} - v{self.version_number}"

