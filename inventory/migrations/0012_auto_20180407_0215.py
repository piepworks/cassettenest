# Generated by Django 2.0.2 on 2018-04-07 02:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0011_rename_models"),
    ]

    operations = [
        migrations.RenameField(
            model_name="roll",
            old_name="name",
            new_name="film",
        ),
    ]
