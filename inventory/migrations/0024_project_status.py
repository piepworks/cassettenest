# Generated by Django 2.0.2 on 2018-07-30 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0023_auto_20180615_1744"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[("current", "Current"), ("archived", "Archived")],
                default="current",
                max_length=20,
            ),
        ),
    ]
