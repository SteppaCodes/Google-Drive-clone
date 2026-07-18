from django.db import models

from apps.accounts.models import User
from apps.common.models import BaseModel


class Folder(BaseModel):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey("self", null=True, blank=True, related_name="subfolders", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_descendants(self, include_self=True):
        """
        Recursively retrieve all child folders using a highly scalable database-level
        Recursive Common Table Expression (CTE). Works natively on PostgreSQL and SQLite.
        """
        from django.db import connection

        # Database-agnostic UUID handling
        param = self.id.hex if connection.vendor == 'sqlite' else str(self.id)

        query = """
            WITH RECURSIVE folder_tree AS (
                SELECT id FROM folders_folder WHERE id = %s
                UNION ALL
                SELECT f.id FROM folders_folder f
                INNER JOIN folder_tree ft ON f.folder_id = ft.id
            )
            SELECT id FROM folder_tree;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [param])
            rows = cursor.fetchall()

        folder_ids = [row[0] for row in rows]

        if not include_self:
            self_str = self.id.hex if connection.vendor == 'sqlite' else str(self.id)
            folder_ids = [fid for fid in folder_ids if str(fid) != self_str]

        return list(Folder.objects.filter(id__in=folder_ids))




