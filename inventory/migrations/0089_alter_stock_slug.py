# Generated by Django 5.0.1 on 2024-01-31 22:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0088_profile_donation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stock",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]
