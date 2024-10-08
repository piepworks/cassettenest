# Generated by Django 3.2 on 2021-05-16 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0067_auto_20210513_1734"),
    ]

    operations = [
        migrations.AlterField(
            model_name="frame",
            name="aperture",
            field=models.CharField(
                blank=True, help_text="Preset dropdown will be ignored.", max_length=20
            ),
        ),
        migrations.AlterField(
            model_name="frame",
            name="shutter_speed",
            field=models.CharField(
                blank=True, help_text="Preset dropdown will be ignored.", max_length=20
            ),
        ),
    ]
