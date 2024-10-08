# Generated by Django 3.1.4 on 2021-01-26 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0058_auto_20210126_1729"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="subscription",
            field=models.CharField(
                choices=[
                    ("none", "None"),
                    ("monthly", "Monthly"),
                    ("annual", "Annual"),
                ],
                default="none",
                max_length=20,
            ),
        ),
    ]
