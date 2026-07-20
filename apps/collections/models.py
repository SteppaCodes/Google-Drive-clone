from django.db import models

from apps.accounts.models import Principal
from apps.common.models import BaseModel


class Collection(BaseModel):
    """
    A Collection is the organizational home for artifacts.

    Humans navigate Lore through nested collections (the familiar folder
    hierarchy).  An artifact always has at most one ``collection_id`` —
    its location in the tree.  Collections also carry the default
    permission set that artifacts inherit when ``inherit_permissions``
    is True.
    """

    name = models.CharField(max_length=200)
    owner = models.ForeignKey(Principal, on_delete=models.CASCADE, related_name="collections")
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_descendants(self, include_self=True):
        """
        Recursively retrieve all child collections using a highly scalable
        database-level Recursive Common Table Expression (CTE).
        Works natively on PostgreSQL and SQLite.
        """
        from django.db import connection

        # Database-agnostic UUID handling
        param = self.id.hex if connection.vendor == 'sqlite' else str(self.id)

        query = """
            WITH RECURSIVE collection_tree AS (
                SELECT id FROM collections_collection WHERE id = %s
                UNION ALL
                SELECT c.id FROM collections_collection c
                INNER JOIN collection_tree ct ON c.parent_id = ct.id
            )
            SELECT id FROM collection_tree;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [param])
            rows = cursor.fetchall()

        collection_ids = [row[0] for row in rows]

        if not include_self:
            self_str = self.id.hex if connection.vendor == 'sqlite' else str(self.id)
            collection_ids = [cid for cid in collection_ids if str(cid) != self_str]

        return list(Collection.objects.filter(id__in=collection_ids))
