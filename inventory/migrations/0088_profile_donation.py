# Generated by Django 4.2.7 on 2023-11-08 23:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0087_remove_profile_friend_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="donation",
            field=models.BooleanField(
                default=False, help_text="This person has given us money"
            ),
        ),
    ]