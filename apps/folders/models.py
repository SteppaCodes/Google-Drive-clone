from django.db import models
from django.contrib.contenttypes.fields import  GenericRelation


from apps.common.models import BaseModel#, StarredItem
from apps.accounts.models import User

class Folder(BaseModel):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)


    def __str__(self):
        return self.name

# Folder.starred_items = GenericRelation(StarredItem, related_query_name='folder_starred_items')