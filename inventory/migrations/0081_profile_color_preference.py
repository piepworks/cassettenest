# Generated by Django 4.1.6 on 2023-02-03 19:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0080_alter_profile_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="color_preference",
            field=models.CharField(
                choices=[("auto", "Automatic"), ("light", "Light"), ("dark", "Dark")],
                default="auto",
                max_length=5,
            ),
        ),
    ]
