# Generated by Django 2.1 on 2018-09-29 22:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0031_auto_20180912_2155"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="manufacturer",
            options={"ordering": ["name"]},
        ),
    ]
