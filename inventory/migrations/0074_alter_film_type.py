# Generated by Django 3.2.6 on 2021-08-11 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0073_alter_film_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='film',
            name='type',
            field=models.CharField(blank=True, choices=[('c41', 'C41 Color'), ('bw', 'Black and White'), ('e6', 'E6 Color Reversal')], max_length=20),
        ),
    ]