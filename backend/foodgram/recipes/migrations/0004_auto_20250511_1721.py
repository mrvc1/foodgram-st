# Generated by Django 3.2.16 on 2025-05-11 14:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_ingredient_ingredient_name_idx'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='tags',
        ),
        migrations.DeleteModel(
            name='Tag',
        ),
    ]
