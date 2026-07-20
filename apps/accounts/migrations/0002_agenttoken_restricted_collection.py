import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('collections', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='agenttoken',
            name='restricted_collection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='collections.collection'),
        ),
    ]
