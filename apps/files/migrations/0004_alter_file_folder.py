# Generated by Django 5.0.1 on 2024-01-31 22:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0003_file_folder'),
        ('folders', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='folder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='files', to='folders.folder'),
        ),
    ]
